"""Data Access activities — 10 business verb operations + backward-compat shim.

Run on DATA_ACCESS_QUEUE. Each activity uses SQLAlchemy Core query builder
with asyncpg for typed, parameterized SQL against the unlock schema in Supabase.

Business verbs follow the Righting Software test: "If I switched from PostgreSQL
to a graph database, would this operation name still make sense?"
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, insert, select, update
from temporalio import activity
from unlock_shared.data_models import (
    CatalogContentRequest,
    CatalogContentResult,
    ClosePipelineRunRequest,
    ClosePipelineRunResult,
    EnrollMemberRequest,
    EnrollMemberResult,
    IdentifyContactRequest,
    IdentifyContactResult,
    LogCommunicationRequest,
    LogCommunicationResult,
    OpenPipelineRunRequest,
    OpenPipelineRunResult,
    ProfileContactRequest,
    ProfileContactResult,
    RecordEngagementRequest,
    RecordEngagementResult,
    RegisterParticipationRequest,
    RegisterParticipationResult,
    SurveyEngagementRequest,
    SurveyEngagementResult,
)

from unlock_data_access.client import get_engine
from unlock_data_access.tables import (
    channel_identities,
    channels,
    content,
    engagements,
    event_participations,
    events,
    memberships,
    message_recipients,
    messages,
    organizations,
    people,
    person_emails,
    person_locations,
    person_names,
    person_phones,
    pipeline_runs,
    source_mappings,
    sources,
)

# ============================================================================
# Helpers: resolve source_key/channel_key to UUIDs
# ============================================================================


async def _resolve_source(conn, source_key: str):
    """Look up source UUID by key. Returns row or None."""
    result = await conn.execute(
        select(sources.c.id).where(sources.c.source_key == source_key)
    )
    return result.fetchone()


async def _resolve_channel(conn, channel_key: str):
    """Look up channel UUID by key. Returns row or None."""
    result = await conn.execute(
        select(channels.c.id).where(channels.c.channel_key == channel_key)
    )
    return result.fetchone()


async def _find_mapping(conn, source_id, external_id: str, entity_type: str):
    """Look up source_mapping. Returns row with internal_id or None."""
    result = await conn.execute(
        select(source_mappings.c.internal_id).where(
            source_mappings.c.source_id == source_id,
            source_mappings.c.external_id == external_id,
            source_mappings.c.entity_type == entity_type,
        )
    )
    return result.fetchone()


# ============================================================================
# identify_contact
# ============================================================================


@activity.defn
async def identify_contact(request: IdentifyContactRequest) -> IdentifyContactResult:
    """Resolve an external identity to an internal person."""
    try:
        async with get_engine().begin() as conn:
            # Resolve source
            src = await _resolve_source(conn, request.source_key)
            if not src:
                return IdentifyContactResult(
                    success=False, message=f"Unknown source: {request.source_key}"
                )
            source_id = src[0]

            # Resolve channel (optional)
            channel_id = None
            if request.channel_key:
                ch = await _resolve_channel(conn, request.channel_key)
                if ch:
                    channel_id = ch[0]

            # Check if mapping exists
            existing = await _find_mapping(conn, source_id, request.external_id, "person")
            if existing:
                return IdentifyContactResult(
                    success=True,
                    message="Existing contact found",
                    person_id=str(existing[0]),
                    is_new=False,
                    source_key=request.source_key,
                )

            # Create new person
            now = datetime.now(UTC)
            person_data = {
                "display_name": request.display_name,
                "title": request.title,
                "company_name": request.company_name,
                "industry": request.industry,
                "bio": request.bio,
                "avatar_url": request.avatar_url,
                "website_url": request.website_url,
                "tags": request.tags,
                "first_seen_at": now,
                "last_seen_at": now,
            }
            # Set primary email from first email if provided
            if request.emails:
                primary = next((e for e in request.emails if e.is_primary), request.emails[0])
                person_data["primary_email"] = primary.email

            result = await conn.execute(
                insert(people).values(**person_data).returning(people.c.id)
            )
            person_row = result.fetchone()
            person_id = str(person_row[0])

            # Create source mapping
            await conn.execute(
                insert(source_mappings).values(
                    source_id=source_id,
                    external_id=request.external_id,
                    entity_type="person",
                    internal_id=person_id,
                )
            )

            # Create channel identity if channel provided
            if channel_id and (request.platform_user_id or request.username):
                await conn.execute(
                    insert(channel_identities).values(
                        person_id=person_id,
                        channel_id=channel_id,
                        platform_user_id=request.platform_user_id,
                        username=request.username,
                        profile_url=request.profile_url,
                        display_name=request.display_name,
                    )
                )

            # Insert person history records
            if request.names:
                for name in request.names:
                    await conn.execute(
                        insert(person_names).values(
                            person_id=person_id,
                            first_name=name.first_name,
                            last_name=name.last_name,
                            display_name=name.display_name,
                            name_type=name.name_type,
                            source_id=source_id,
                            channel_id=channel_id,
                            is_current=name.is_current,
                            observed_at=name.observed_at or now,
                        )
                    )

            if request.emails:
                for email_rec in request.emails:
                    await conn.execute(
                        insert(person_emails).values(
                            person_id=person_id,
                            email=email_rec.email,
                            email_type=email_rec.email_type,
                            is_primary=email_rec.is_primary,
                            is_verified=email_rec.is_verified,
                            source_id=source_id,
                            channel_id=channel_id,
                            observed_at=email_rec.observed_at or now,
                        )
                    )

            if request.phones:
                for phone_rec in request.phones:
                    await conn.execute(
                        insert(person_phones).values(
                            person_id=person_id,
                            phone=phone_rec.phone,
                            phone_type=phone_rec.phone_type,
                            is_primary=phone_rec.is_primary,
                            source_id=source_id,
                            observed_at=phone_rec.observed_at or now,
                        )
                    )

            if request.locations:
                for loc in request.locations:
                    await conn.execute(
                        insert(person_locations).values(
                            person_id=person_id,
                            city=loc.city,
                            state=loc.state,
                            country=loc.country,
                            zip_code=loc.zip_code,
                            location_type=loc.location_type,
                            is_current=loc.is_current,
                            source_id=source_id,
                            observed_at=loc.observed_at or now,
                        )
                    )

            return IdentifyContactResult(
                success=True,
                message="New contact created",
                person_id=person_id,
                is_new=True,
                source_key=request.source_key,
            )
    except Exception as e:
        return IdentifyContactResult(
            success=False, message=f"identify_contact failed: {e}"
        )


# ============================================================================
# catalog_content
# ============================================================================


@activity.defn
async def catalog_content(request: CatalogContentRequest) -> CatalogContentResult:
    """Register content items in the engagement graph with dedup."""
    try:
        async with get_engine().begin() as conn:
            src = await _resolve_source(conn, request.source_key)
            if not src:
                return CatalogContentResult(
                    success=False, message=f"Unknown source: {request.source_key}"
                )
            source_id = src[0]

            created = 0
            updated = 0
            skipped = 0

            for record in request.records:
                # Resolve channel
                ch = await _resolve_channel(conn, record.channel_key)
                if not ch:
                    skipped += 1
                    continue
                channel_id = ch[0]

                # Check dedup via source_mappings
                if record.external_id:
                    existing = await _find_mapping(
                        conn, source_id, record.external_id, "content"
                    )
                    if existing:
                        skipped += 1
                        continue

                # Insert content
                content_data = {
                    "channel_id": channel_id,
                    "source_id": source_id,
                    "content_type": record.content_type,
                    "title": record.title,
                    "body": record.body,
                    "url": record.url,
                    "published_at": record.published_at,
                    "language": record.language,
                    "is_public": record.is_public,
                    "media_type": record.media_type,
                    "thumbnail_url": record.thumbnail_url,
                    "conversation_thread_id": record.conversation_thread_id,
                    "like_count": record.like_count,
                    "comment_count": record.comment_count,
                    "share_count": record.share_count,
                    "view_count": record.view_count,
                    "impression_count": record.impression_count,
                    "reach_count": record.reach_count,
                    "bookmark_count": record.bookmark_count,
                    "retweet_count": record.retweet_count,
                    "reply_count": record.reply_count,
                    "quote_count": record.quote_count,
                    "tags": record.tags,
                }
                if record.pipeline_run_id:
                    content_data["pipeline_run_id"] = record.pipeline_run_id

                # Compute word count
                if record.body:
                    content_data["word_count"] = len(record.body.split())

                result = await conn.execute(
                    insert(content).values(**content_data).returning(content.c.id)
                )
                content_row = result.fetchone()
                content_id = str(content_row[0])

                # Create source mapping for dedup
                if record.external_id:
                    await conn.execute(
                        insert(source_mappings).values(
                            source_id=source_id,
                            external_id=record.external_id,
                            entity_type="content",
                            internal_id=content_id,
                        )
                    )

                created += 1

            return CatalogContentResult(
                success=True,
                message=f"Cataloged {created} content items",
                created=created,
                updated=updated,
                skipped=skipped,
            )
    except Exception as e:
        return CatalogContentResult(
            success=False, message=f"catalog_content failed: {e}"
        )


# ============================================================================
# record_engagement
# ============================================================================


@activity.defn
async def record_engagement(
    request: RecordEngagementRequest,
) -> RecordEngagementResult:
    """Capture person+content interactions in batch."""
    try:
        async with get_engine().begin() as conn:
            src = await _resolve_source(conn, request.source_key)
            if not src:
                return RecordEngagementResult(
                    success=False, message=f"Unknown source: {request.source_key}"
                )
            source_id = src[0]

            recorded = 0
            skipped = 0

            for record in request.records:
                ch = await _resolve_channel(conn, record.channel_key)
                if not ch:
                    skipped += 1
                    continue
                channel_id = ch[0]

                # Resolve person
                person_row = await _find_mapping(
                    conn, source_id, record.person_external_id, "person"
                )
                if not person_row:
                    skipped += 1
                    continue
                person_id = person_row[0]

                # Resolve content
                content_row = await _find_mapping(
                    conn, source_id, record.content_external_id, "content"
                )
                if not content_row:
                    skipped += 1
                    continue
                content_id = content_row[0]

                await conn.execute(
                    insert(engagements).values(
                        person_id=person_id,
                        content_id=content_id,
                        channel_id=channel_id,
                        source_id=source_id,
                        pipeline_run_id=record.pipeline_run_id,
                        engagement_type=record.engagement_type,
                        occurred_at=record.occurred_at,
                        comment_text=record.comment_text,
                        media_url=record.media_url,
                        media_type=record.media_type,
                        reaction_type=record.reaction_type,
                        referrer_url=record.referrer_url,
                        target_url=record.target_url,
                        duration_seconds=record.duration_seconds,
                        device_type=record.device_type,
                        browser=record.browser,
                        os=record.os,
                        utm_source=record.utm_source,
                        utm_medium=record.utm_medium,
                        utm_campaign=record.utm_campaign,
                        ip_address_hash=record.ip_address_hash,
                    )
                )
                recorded += 1

            return RecordEngagementResult(
                success=True,
                message=f"Recorded {recorded} engagements, skipped {skipped}",
                recorded=recorded,
                skipped=skipped,
            )
    except Exception as e:
        return RecordEngagementResult(
            success=False, message=f"record_engagement failed: {e}"
        )


# ============================================================================
# log_communication
# ============================================================================


@activity.defn
async def log_communication(
    request: LogCommunicationRequest,
) -> LogCommunicationResult:
    """Capture person-to-person messages with recipients."""
    try:
        async with get_engine().begin() as conn:
            src = await _resolve_source(conn, request.source_key)
            if not src:
                return LogCommunicationResult(
                    success=False, message=f"Unknown source: {request.source_key}"
                )
            source_id = src[0]

            logged = 0
            skipped = 0

            for record in request.records:
                ch = await _resolve_channel(conn, record.channel_key)
                if not ch:
                    skipped += 1
                    continue
                channel_id = ch[0]

                # Resolve sender
                sender_row = await _find_mapping(
                    conn, source_id, record.sender_external_id, "person"
                )
                if not sender_row:
                    skipped += 1
                    continue
                sender_id = sender_row[0]

                # Insert message
                result = await conn.execute(
                    insert(messages)
                    .values(
                        sender_id=sender_id,
                        channel_id=channel_id,
                        source_id=source_id,
                        pipeline_run_id=record.pipeline_run_id,
                        subject=record.subject,
                        body_plain=record.body_plain,
                        body_html=record.body_html,
                        sent_at=record.sent_at,
                        is_read=record.is_read,
                        thread_id=record.thread_id,
                        folder=record.folder,
                        labels=record.labels,
                        is_automated=record.is_automated,
                    )
                    .returning(messages.c.id)
                )
                msg_row = result.fetchone()
                msg_id = str(msg_row[0])

                # Insert recipients
                for recipient_list, rtype in [
                    (record.recipient_ids, "to"),
                    (record.cc_ids, "cc"),
                    (record.bcc_ids, "bcc"),
                ]:
                    if not recipient_list:
                        continue
                    for ext_id in recipient_list:
                        rcpt = await _find_mapping(conn, source_id, ext_id, "person")
                        if rcpt:
                            await conn.execute(
                                insert(message_recipients).values(
                                    message_id=msg_id,
                                    person_id=rcpt[0],
                                    recipient_type=rtype,
                                )
                            )

                logged += 1

            return LogCommunicationResult(
                success=True,
                message=f"Logged {logged} communications",
                logged=logged,
                skipped=skipped,
            )
    except Exception as e:
        return LogCommunicationResult(
            success=False, message=f"log_communication failed: {e}"
        )


# ============================================================================
# register_participation
# ============================================================================


@activity.defn
async def register_participation(
    request: RegisterParticipationRequest,
) -> RegisterParticipationResult:
    """Record event attendance/completion."""
    try:
        async with get_engine().begin() as conn:
            src = await _resolve_source(conn, request.source_key)
            if not src:
                return RegisterParticipationResult(
                    success=False, message=f"Unknown source: {request.source_key}"
                )
            source_id = src[0]

            registered = 0
            updated = 0
            skipped = 0

            for record in request.records:
                # Resolve person
                person_row = await _find_mapping(
                    conn, source_id, record.person_external_id, "person"
                )
                if not person_row:
                    skipped += 1
                    continue
                person_id = person_row[0]

                # Find event by title
                event_result = await conn.execute(
                    select(events.c.id).where(events.c.title == record.event_title)
                )
                event_row = event_result.fetchone()
                if not event_row:
                    skipped += 1
                    continue
                event_id = event_row[0]

                # Insert participation
                await conn.execute(
                    insert(event_participations).values(
                        person_id=person_id,
                        event_id=event_id,
                        source_id=source_id,
                        participation_type=record.participation_type,
                        registered_at=record.registered_at,
                        attended_at=record.attended_at,
                        completed_at=record.completed_at,
                        feedback_score=record.feedback_score,
                        feedback_text=record.feedback_text,
                        certificate_url=record.certificate_url,
                        notes=record.notes,
                    )
                )
                registered += 1

            return RegisterParticipationResult(
                success=True,
                message=f"Registered {registered} participations",
                registered=registered,
                updated=updated,
                skipped=skipped,
            )
    except Exception as e:
        return RegisterParticipationResult(
            success=False, message=f"register_participation failed: {e}"
        )


# ============================================================================
# enroll_member
# ============================================================================


@activity.defn
async def enroll_member(request: EnrollMemberRequest) -> EnrollMemberResult:
    """Record organizational affiliation."""
    try:
        async with get_engine().begin() as conn:
            src = await _resolve_source(conn, request.source_key)
            if not src:
                return EnrollMemberResult(
                    success=False, message=f"Unknown source: {request.source_key}"
                )
            source_id = src[0]

            enrolled = 0
            updated = 0
            skipped = 0

            for record in request.records:
                # Resolve person
                person_row = await _find_mapping(
                    conn, source_id, record.person_external_id, "person"
                )
                if not person_row:
                    skipped += 1
                    continue
                person_id = person_row[0]

                # Find or create organization
                org_result = await conn.execute(
                    select(organizations.c.id).where(
                        organizations.c.name == record.organization_name
                    )
                )
                org_row = org_result.fetchone()
                if org_row:
                    org_id = org_row[0]
                else:
                    org_insert = await conn.execute(
                        insert(organizations)
                        .values(
                            name=record.organization_name,
                            organization_type=record.organization_type,
                        )
                        .returning(organizations.c.id)
                    )
                    org_id = org_insert.fetchone()[0]

                # Insert membership
                await conn.execute(
                    insert(memberships).values(
                        person_id=person_id,
                        organization_id=org_id,
                        source_id=source_id,
                        role=record.role,
                        department=record.department,
                        started_at=record.started_at,
                        ended_at=record.ended_at,
                        is_active=record.is_active,
                        notes=record.notes,
                        tags=record.tags,
                    )
                )
                enrolled += 1

            return EnrollMemberResult(
                success=True,
                message=f"Enrolled {enrolled} memberships",
                enrolled=enrolled,
                updated=updated,
                skipped=skipped,
            )
    except Exception as e:
        return EnrollMemberResult(
            success=False, message=f"enroll_member failed: {e}"
        )


# ============================================================================
# profile_contact
# ============================================================================


@activity.defn
async def profile_contact(request: ProfileContactRequest) -> ProfileContactResult:
    """Assemble a unified contact view across all channels."""
    try:
        async with get_engine().begin() as conn:
            person_id = request.person_id

            # Resolve person_id from email if not provided directly
            if not person_id and request.email:
                email_result = await conn.execute(
                    select(person_emails.c.person_id).where(
                        person_emails.c.email == request.email
                    )
                )
                email_row = email_result.fetchone()
                if not email_row:
                    return ProfileContactResult(
                        success=False, message="Contact not found by email"
                    )
                person_id = str(email_row[0])

            # Resolve from source mapping
            if not person_id and request.external_id and request.source_key:
                src = await _resolve_source(conn, request.source_key)
                if src:
                    mapping = await _find_mapping(
                        conn, src[0], request.external_id, "person"
                    )
                    if mapping:
                        person_id = str(mapping[0])

            if not person_id:
                return ProfileContactResult(
                    success=False, message="Contact not found"
                )

            # Fetch person core
            person_result = await conn.execute(
                select(people).where(people.c.id == person_id)
            )
            person_row = person_result.fetchone()
            if not person_row:
                return ProfileContactResult(
                    success=False, message="Contact not found"
                )

            # Fetch history records
            names_result = await conn.execute(
                select(person_names).where(person_names.c.person_id == person_id)
            )
            emails_result = await conn.execute(
                select(person_emails).where(person_emails.c.person_id == person_id)
            )
            phones_result = await conn.execute(
                select(person_phones).where(person_phones.c.person_id == person_id)
            )
            locations_result = await conn.execute(
                select(person_locations).where(
                    person_locations.c.person_id == person_id
                )
            )

            # Fetch identities
            identities_result = await conn.execute(
                select(channel_identities).where(
                    channel_identities.c.person_id == person_id
                )
            )

            # Engagement summary
            engagement_result = await conn.execute(
                select(
                    engagements.c.engagement_type,
                    func.count().label("count"),
                )
                .where(engagements.c.person_id == person_id)
                .group_by(engagements.c.engagement_type)
            )

            # Memberships
            membership_result = await conn.execute(
                select(
                    memberships.c.role,
                    memberships.c.is_active,
                    organizations.c.name.label("organization_name"),
                )
                .select_from(memberships.join(organizations))
                .where(memberships.c.person_id == person_id)
            )

            # Build response — extract row data via helper
            def _rows(result):
                return [
                    dict(r._data) if hasattr(r, "_data") else r
                    for r in result.fetchall()
                ]

            def _attr(row, name):
                if hasattr(row, "_data"):
                    return row._data.get(name)
                if hasattr(row, name):
                    return getattr(row, name)
                return row.get(name) if hasattr(row, "get") else None

            eng_summary = {}
            for row in engagement_result.fetchall():
                etype = _attr(row, "engagement_type")
                eng_summary[etype] = _attr(row, "count")

            return ProfileContactResult(
                success=True,
                message="Contact profile assembled",
                person_id=person_id,
                display_name=_attr(person_row, "display_name"),
                primary_email=_attr(person_row, "primary_email"),
                title=_attr(person_row, "title"),
                company_name=_attr(person_row, "company_name"),
                bio=_attr(person_row, "bio"),
                names=_rows(names_result),
                emails=_rows(emails_result),
                phones=_rows(phones_result),
                locations=_rows(locations_result),
                identities=_rows(identities_result),
                engagement_summary=eng_summary,
                membership_summary=_rows(membership_result),
                first_seen_at=_attr(person_row, "first_seen_at"),
                last_seen_at=_attr(person_row, "last_seen_at"),
                tags=_attr(person_row, "tags"),
            )
    except Exception as e:
        return ProfileContactResult(
            success=False, message=f"profile_contact failed: {e}"
        )


# ============================================================================
# survey_engagement
# ============================================================================


@activity.defn
async def survey_engagement(
    request: SurveyEngagementRequest,
) -> SurveyEngagementResult:
    """Take a broad view of engagement data with filters."""
    try:
        async with get_engine().begin() as conn:
            # Build WHERE conditions
            conditions = []
            if request.channel_key:
                ch = await _resolve_channel(conn, request.channel_key)
                if ch:
                    conditions.append(engagements.c.channel_id == ch[0])
            if request.engagement_type:
                conditions.append(
                    engagements.c.engagement_type == request.engagement_type
                )
            if request.person_id:
                conditions.append(engagements.c.person_id == request.person_id)
            if request.since:
                conditions.append(engagements.c.occurred_at >= request.since)
            if request.until:
                conditions.append(engagements.c.occurred_at <= request.until)

            # Count query
            count_q = select(func.count()).select_from(engagements)
            for cond in conditions:
                count_q = count_q.where(cond)
            count_result = await conn.execute(count_q)
            total_count_row = count_result.fetchone()
            total_count = total_count_row[0] if total_count_row else 0

            # Data query
            data_q = select(engagements).order_by(engagements.c.occurred_at.desc())
            for cond in conditions:
                data_q = data_q.where(cond)
            data_q = data_q.limit(request.limit).offset(request.offset)

            data_result = await conn.execute(data_q)
            rows = data_result.fetchall()

            records = []
            for row in rows:
                if hasattr(row, '_data'):
                    records.append(row._data)
                else:
                    records.append(dict(row) if hasattr(row, 'keys') else row)

            has_more = (request.offset + request.limit) < total_count

            return SurveyEngagementResult(
                success=True,
                message=f"Found {total_count} engagements",
                records=records,
                total_count=total_count,
                has_more=has_more,
            )
    except Exception as e:
        return SurveyEngagementResult(
            success=False, message=f"survey_engagement failed: {e}"
        )


# ============================================================================
# open_pipeline_run
# ============================================================================


@activity.defn
async def open_pipeline_run(
    request: OpenPipelineRunRequest,
) -> OpenPipelineRunResult:
    """Start tracking an ingestion execution."""
    try:
        async with get_engine().begin() as conn:
            src = await _resolve_source(conn, request.source_key)
            if not src:
                return OpenPipelineRunResult(
                    success=False, message=f"Unknown source: {request.source_key}"
                )
            source_id = src[0]

            result = await conn.execute(
                insert(pipeline_runs)
                .values(
                    source_id=source_id,
                    workflow_run_id=request.workflow_run_id,
                    status="running",
                    resource_type=request.resource_type,
                )
                .returning(pipeline_runs.c.id)
            )
            run_row = result.fetchone()

            return OpenPipelineRunResult(
                success=True,
                message="Pipeline run opened",
                pipeline_run_id=str(run_row[0]),
            )
    except Exception as e:
        return OpenPipelineRunResult(
            success=False, message=f"open_pipeline_run failed: {e}"
        )


# ============================================================================
# close_pipeline_run
# ============================================================================


@activity.defn
async def close_pipeline_run(
    request: ClosePipelineRunRequest,
) -> ClosePipelineRunResult:
    """Complete ingestion tracking with stats."""
    try:
        async with get_engine().begin() as conn:
            now = datetime.now(UTC)

            result = await conn.execute(
                update(pipeline_runs)
                .where(pipeline_runs.c.id == request.pipeline_run_id)
                .values(
                    status=request.status,
                    record_count=request.record_count,
                    records_created=request.records_created,
                    records_updated=request.records_updated,
                    records_skipped=request.records_skipped,
                    error_message=request.error_message,
                    pages_fetched=request.pages_fetched,
                    completed_at=now,
                )
                .returning(pipeline_runs.c.id, pipeline_runs.c.started_at)
            )
            run_row = result.fetchone()
            if not run_row:
                return ClosePipelineRunResult(
                    success=False,
                    message=f"Pipeline run not found: {request.pipeline_run_id}",
                )

            # Calculate duration
            duration = None
            if hasattr(run_row, "_data"):
                started_at = run_row._data.get("started_at")
                run_id = run_row._data.get(
                    "id", request.pipeline_run_id
                )
            else:
                started_at = run_row[1] if len(run_row) > 1 else None
                run_id = run_row[0]
            if started_at and isinstance(started_at, datetime):
                duration = (now - started_at).total_seconds()

            return ClosePipelineRunResult(
                success=True,
                message="Pipeline run closed",
                pipeline_run_id=str(run_id),
                duration_seconds=duration,
            )
    except Exception as e:
        return ClosePipelineRunResult(
            success=False, message=f"close_pipeline_run failed: {e}"
        )


# ============================================================================
# hello_store_data (backward compatibility shim)
# ============================================================================


@activity.defn
async def hello_store_data(transformed_data: str) -> str:
    """Deprecated: simulates storing transformed data.

    Kept for backward compatibility with IngestWorkflow which calls this
    activity on DATA_ACCESS_QUEUE. Will be replaced when DATA_MGR wires
    workflows to the new business verb activities.
    """
    activity.logger.info(f"Data Access: storing '{transformed_data[:50]}'")
    return f"Stored: {transformed_data}"
