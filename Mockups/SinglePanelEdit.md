The code below contains a design. This design should be used to create a new app or be added to an existing one.

Look at the current open project to determine if a project exists. If no project is open, create a new Vite project then create this view in React after componentizing it.

If a project does exist, determine the framework being used and implement the design within that framework. Identify whether reusable components already exist that can be used to implement the design faithfully and if so use them, otherwise create new components. If other views already exist in the project, make sure to place the view in a sensible route and connect it to the other views.

Ensure the visual characteristics, layout, and interactions in the design are preserved with perfect fidelity.

Run the dev command so the user can see the app once finished.

```html
<html lang="en" vid="0"><head vid="1">
    <meta charset="UTF-8" vid="2">
    <meta name="viewport" content="width=device-width, initial-scale=1.0" vid="3">
    <title vid="4">Q4 Revenue Metrics - Panel Configuration</title>
    <script src="https://cdn.tailwindcss.com/3.4.17" vid="5"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com" vid="6">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="" vid="7">
    <link href="https://fonts.googleapis.com/css2?family=Anton&amp;family=Space+Mono:ital,wght@0,400;0,700;1,400&amp;family=Playfair+Display:ital@1&amp;display=swap" rel="stylesheet" vid="8">
    <script vid="9">
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        charcoal: '#121212',
                        offwhite: '#f5f5f1',
                        sage: '#dbe4d0',
                        coral: '#ea6d58',
                        'charcoal-light': '#1a1a1a',
                    },
                    fontFamily: {
                        display: ['Anton', 'sans-serif'],
                        mono: ['Space Mono', 'monospace'],
                        serif: ['Playfair Display', 'serif'],
                    }
                }
            }
        }
    </script>
    <style vid="10">
        body {
            background-color: #121212;
            color: #f5f5f1;
        }
        .no-scrollbar::-webkit-scrollbar {
            display: none;
        }
        .no-scrollbar {
            -ms-overflow-style: none;
            scrollbar-width: none;
        }
        .scrim-overlay {
            background-color: rgba(18, 18, 18, 0.7);
            backdrop-filter: blur(2px);
        }
        .config-input {
            background: #1a1a1a;
            border: 1px solid rgba(255,255,255,0.1);
            color: #f5f5f1;
            font-size: 10px;
            padding: 6px 10px;
            outline: none;
        }
        .config-input:focus {
            border-color: #ea6d58;
        }
        .active-tab {
            color: #ea6d58;
            border-bottom: 1px solid #ea6d58;
        }
    </style>
</head>
<body class="h-screen w-screen overflow-hidden flex bg-charcoal font-mono selection:bg-coral selection:text-charcoal" vid="11">

    <nav class="w-24 border-r border-white/10 flex flex-col justify-between items-center py-8 z-50 bg-charcoal shrink-0" vid="12">
        <div class="w-10 h-10 text-sage opacity-30" vid="13">
            <svg viewBox="0 0 100 100" fill="currentColor" vid="14">
                <rect x="10" y="10" width="35" height="80" vid="15"></rect>
                <rect x="55" y="10" width="35" height="50" vid="16"></rect>
            </svg>
        </div>
        <div class="flex flex-col gap-12 items-center opacity-30" vid="17">
            <div class="text-white/40 transform -rotate-90 text-sm tracking-widest" vid="18">PUBLIC</div>
            <div class="w-[1px] h-12 bg-white/10" vid="19"></div>
            <div class="text-white/40 transform -rotate-90 text-sm tracking-widest" vid="20">SHARED</div>
            <div class="w-[1px] h-12 bg-white/10" vid="21"></div>
            <div class="text-coral transform -rotate-90 text-sm tracking-widest" vid="22">PERSONAL</div>
        </div>
        <div class="w-10 h-10 rounded-full border border-white/20 p-1 opacity-30" vid="23">
            <div class="w-full h-full rounded-full bg-cover bg-center grayscale" style="background-image: url('https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&amp;w=150&amp;auto=format&amp;fit=crop');" vid="24"></div>
        </div>
    </nav>

    <main class="flex-1 flex flex-col h-full overflow-hidden relative" vid="25">
        <header class="h-20 border-b border-white/10 flex items-center justify-between px-12 bg-charcoal z-40 shrink-0" vid="26">
            <div class="flex items-center gap-4 text-xs tracking-widest uppercase text-white/50" vid="27">
                <span vid="28">Back to Views</span>
                <span vid="29">/</span>
                <span class="text-coral" vid="30">Q4 Revenue Metrics</span>
                <span class="ml-4 px-2 py-0.5 bg-coral/10 text-coral text-[9px] border border-coral/20 rounded-sm" vid="31">EDITING PANEL</span>
            </div>
            
            <div class="flex items-center gap-4" vid="32">
                <button class="px-6 py-2 bg-coral text-charcoal font-bold text-[10px] tracking-[0.2em] uppercase hover:bg-sage transition-all" vid="33">Apply Changes</button>
                <button class="px-4 py-2 border border-white/10 text-[10px] tracking-[0.2em] uppercase text-white/60 hover:text-white transition-all" vid="34">Cancel</button>
            </div>
        </header>

        <div class="flex-1 overflow-y-auto no-scrollbar scroll-smooth relative" vid="35">
            
            <div class="scrim-overlay absolute inset-0 z-10" vid="36"></div>
            
            <section class="p-12 border-b border-white/10 opacity-20" vid="37">
                <div class="flex flex-col md:flex-row md:items-end justify-between gap-6" vid="38">
                    <div vid="39">
                        <h1 class="text-8xl font-display text-sage uppercase leading-none mb-4" vid="40">Revenue Analysis</h1>
                        <p class="font-serif italic text-white/60 text-xl max-w-2xl" vid="41">Comprehensive tracking of donor pipeline and grant allocation for the final fiscal quarter of 2023.</p>
                    </div>
                </div>
            </section>

            <section class="grid grid-cols-6 border-white/10" vid="42">
                
                <div class="col-span-1 border-r border-b border-white/10 p-8 opacity-10" vid="43"></div>
                <div class="col-span-1 border-r border-b border-white/10 p-8 opacity-10" vid="44"></div>
                <div class="col-span-1 border-r border-b border-white/10 p-8 opacity-10" vid="45"></div>
                <div class="col-span-1 border-r border-b border-white/10 p-8 opacity-10" vid="46"></div>

                
                <div class="col-span-6 min-h-[600px] bg-charcoal-light z-30 relative shadow-[0_0_100px_rgba(0,0,0,0.5)] border-y border-coral/40" vid="47">
                    <div class="grid grid-cols-12 h-full" vid="48">
                        
                        <div class="col-span-5 border-r border-white/5 flex flex-col" vid="49">
                            
                            <div class="flex border-b border-white/5" vid="50">
                                <button class="px-8 py-4 text-[10px] tracking-widest uppercase active-tab font-bold" vid="51">Data</button>
                                <button class="px-8 py-4 text-[10px] tracking-widest uppercase text-white/40 hover:text-white" vid="52">Display</button>
                                <button class="px-8 py-4 text-[10px] tracking-widest uppercase text-white/40 hover:text-white" vid="53">Axes</button>
                                <button class="px-8 py-4 text-[10px] tracking-widest uppercase text-white/40 hover:text-white" vid="54">Thresholds</button>
                            </div>

                            
                            <div class="p-8 space-y-10" vid="55">
                                
                                <div vid="56">
                                    <div class="text-[9px] tracking-widest text-coral uppercase mb-6 flex items-center gap-2" vid="57">
                                        <span class="w-1.5 h-1.5 bg-coral" vid="58"></span> Metric Query
                                    </div>
                                    <div class="space-y-3" vid="59">
                                        <div class="flex flex-col gap-1" vid="60">
                                            <label class="text-[8px] text-white/30 uppercase tracking-tighter" vid="61">Select Metric</label>
                                            <select class="config-input w-full appearance-none bg-charcoal-light" vid="62">
                                                <option vid="63">revenue.total_quarterly_inflow</option>
                                                <option vid="64">revenue.gift_size_avg</option>
                                                <option vid="65">donor.conversion_rate</option>
                                            </select>
                                        </div>
                                        <div class="grid grid-cols-2 gap-3" vid="66">
                                            <div class="flex flex-col gap-1" vid="67">
                                                <label class="text-[8px] text-white/30 uppercase tracking-tighter" vid="68">Aggregation</label>
                                                <select class="config-input w-full appearance-none bg-charcoal-light" vid="69">
                                                    <option vid="70">Sum</option>
                                                    <option vid="71">Average</option>
                                                    <option vid="72">Count</option>
                                                </select>
                                            </div>
                                            <div class="flex flex-col gap-1" vid="73">
                                                <label class="text-[8px] text-white/30 uppercase tracking-tighter" vid="74">Interval</label>
                                                <select class="config-input w-full appearance-none bg-charcoal-light" vid="75">
                                                    <option vid="76">Daily</option>
                                                    <option vid="77">Weekly</option>
                                                    <option vid="78">Monthly</option>
                                                </select>
                                            </div>
                                        </div>
                                        <div class="flex flex-col gap-1 pt-2" vid="79">
                                            <label class="text-[8px] text-white/30 uppercase tracking-tighter" vid="80">Filter By</label>
                                            <div class="flex gap-2" vid="81">
                                                <select class="config-input flex-1 appearance-none bg-charcoal-light" vid="82">
                                                    <option vid="83">channel</option>
                                                    <option vid="84">region</option>
                                                </select>
                                                <span class="text-white/20 self-center text-[10px]" vid="85">IN</span>
                                                <select class="config-input flex-1 appearance-none bg-charcoal-light" vid="86">
                                                    <option vid="87">Direct, Grant, Corporate</option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                
                                <div vid="88">
                                    <div class="text-[9px] tracking-widest text-white/40 uppercase mb-4" vid="89">Comparison</div>
                                    <div class="flex items-center gap-4" vid="90">
                                        <label class="flex items-center gap-2 cursor-pointer" vid="91">
                                            <div class="w-3 h-3 border border-coral flex items-center justify-center" vid="92">
                                                <div class="w-1.5 h-1.5 bg-coral" vid="93"></div>
                                            </div>
                                            <span class="text-[10px] text-white/60" vid="94">Previous Period</span>
                                        </label>
                                        <label class="flex items-center gap-2 cursor-pointer" vid="95">
                                            <div class="w-3 h-3 border border-white/20" vid="96"></div>
                                            <span class="text-[10px] text-white/30" vid="97">Year over Year</span>
                                        </label>
                                    </div>
                                </div>

                                <div class="pt-6 mt-6 border-t border-white/5" vid="98">
                                    <div class="text-[8px] text-white/20 uppercase tracking-[0.2em] mb-4" vid="99">Raw SQL Reference</div>
                                    <div class="bg-black/40 p-4 font-mono text-[9px] text-sage/60 leading-relaxed rounded-sm" vid="100">
                                        SELECT date_trunc('day', created_at), sum(amount) <br vid="101">
                                        FROM ledger.transactions <br vid="102">
                                        WHERE status = 'success' AND period = 'Q4' <br vid="103">
                                        GROUP BY 1 ORDER BY 1 ASC;
                                    </div>
                                </div>
                            </div>
                        </div>

                        
                        <div class="col-span-7 p-12 flex flex-col" vid="104">
                            <div class="flex justify-between items-center mb-12" vid="105">
                                <div vid="106">
                                    <div class="text-[10px] tracking-[0.2em] text-white/40 uppercase" vid="107">Live Preview</div>
                                    <h3 class="text-2xl font-display text-sage mt-1" vid="108">Revenue Over Time (USD)</h3>
                                </div>
                                <div class="flex gap-4" vid="109">
                                    <span class="text-[10px] text-sage flex items-center gap-2" vid="110"><span class="w-2 h-2 rounded-full bg-sage" vid="111"></span> Current</span>
                                    <span class="text-[10px] text-white/20 flex items-center gap-2" vid="112"><span class="w-2 h-2 rounded-full bg-white/10" vid="113"></span> Previous</span>
                                </div>
                            </div>
                            
                            
                            <div class="flex-1 flex items-end justify-between gap-6 relative mb-8" vid="114">
                                <div class="absolute inset-0 flex flex-col justify-between opacity-5" vid="115">
                                    <div class="border-t border-white w-full flex justify-between" vid="116"><span class="text-[8px] -mt-2" vid="117">$1M</span></div>
                                    <div class="border-t border-white w-full flex justify-between" vid="118"><span class="text-[8px] -mt-2" vid="119">$750k</span></div>
                                    <div class="border-t border-white w-full flex justify-between" vid="120"><span class="text-[8px] -mt-2" vid="121">$500k</span></div>
                                    <div class="border-t border-white w-full flex justify-between" vid="122"><span class="text-[8px] -mt-2" vid="123">$250k</span></div>
                                    <div class="border-t border-white w-full" vid="124"></div>
                                </div>
                                <div class="flex-1 bg-white/10 relative h-[45%] hover:bg-coral/20 transition-colors cursor-crosshair group" vid="125">
                                    <div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-charcoal px-2 py-1 text-[8px] border border-white/10 opacity-0 group-hover:opacity-100 whitespace-nowrap" vid="126">OCT 14: $452k</div>
                                </div>
                                <div class="flex-1 bg-white/10 relative h-[68%] hover:bg-coral/20 transition-colors cursor-crosshair group" vid="127"></div>
                                <div class="flex-1 bg-white/10 relative h-[52%] hover:bg-coral/20 transition-colors cursor-crosshair group" vid="128"></div>
                                <div class="flex-1 bg-white/10 relative h-[88%] hover:bg-coral/20 transition-colors cursor-crosshair group" vid="129"></div>
                                <div class="flex-1 bg-white/10 relative h-[98%] hover:bg-coral/20 transition-colors cursor-crosshair group" vid="130"></div>
                                <div class="flex-1 bg-white/10 relative h-[72%] hover:bg-coral/20 transition-colors cursor-crosshair group" vid="131"></div>
                                <div class="flex-1 bg-white/10 relative h-[82%] hover:bg-coral/20 transition-colors cursor-crosshair group" vid="132"></div>
                            </div>
                            <div class="flex justify-between px-2 text-[9px] text-white/20 uppercase tracking-widest" vid="133">
                                <span vid="134">Week 40</span>
                                <span vid="135">Week 41</span>
                                <span vid="136">Week 42</span>
                                <span vid="137">Week 43</span>
                                <span vid="138">Week 44</span>
                                <span vid="139">Week 45</span>
                                <span vid="140">Week 46</span>
                            </div>
                        </div>
                    </div>
                </div>

                
                <div class="col-span-3 border-r border-b border-white/10 p-8 opacity-10" vid="141"></div>
                <div class="col-span-3 border-r border-b border-white/10 p-8 opacity-10" vid="142"></div>
            </section>
        </div>
    </main>

    
    <div class="fixed bottom-12 right-12 bg-charcoal border border-white/10 p-2 shadow-2xl flex flex-col gap-2 z-[100] opacity-30" vid="143">
        <div class="w-10 h-10 flex items-center justify-center text-white/40" vid="144">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" vid="145"><path d="M12 5v14M5 12h14" vid="146"></path></svg>
        </div>
        <div class="w-10 h-10 flex items-center justify-center text-white/40" vid="147">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" vid="148"><rect x="3" y="3" width="18" height="18" rx="2" ry="2" vid="149"></rect></svg>
        </div>
    </div>

</body></html>
```
