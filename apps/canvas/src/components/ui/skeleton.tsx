function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`animate-pulse bg-white/[0.06] ${className ?? ""}`}
      {...props}
    />
  );
}

export { Skeleton };
