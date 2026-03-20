The code below contains a design. This design should be used to create a new app or be added to an existing one.

Look at the current open project to determine if a project exists. If no project is open, create a new Vite project then create this view in React after componentizing it.

If a project does exist, determine the framework being used and implement the design within that framework. Identify whether reusable components already exist that can be used to implement the design faithfully and if so use them, otherwise create new components. If other views already exist in the project, make sure to place the view in a sensible route and connect it to the other views.

Ensure the visual characteristics, layout, and interactions in the design are preserved with perfect fidelity.

Run the dev command so the user can see the app once finished.

```html
<html lang="en" vid="0"><head vid="1">
    <meta charset="UTF-8" vid="2">
    <meta name="viewport" content="width=device-width, initial-scale=1.0" vid="3">
    <title vid="4">Q4 Revenue Metrics - Edit Mode</title>
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
        .edit-panel {
            position: relative;
            transition: all 0.2s ease;
        }
        .edit-panel:hover {
            outline: 1px solid #ea6d58;
            background-color: rgba(234, 109, 88, 0.02);
        }
        .drag-handle {
            position: absolute;
            top: 8px;
            left: 8px;
            opacity: 0;
            cursor: grab;
            transition: opacity 0.2s;
        }
        .edit-panel:hover .drag-handle {
            opacity: 0.6;
        }
        .resize-grip {
            position: absolute;
            bottom: 4px;
            right: 4px;
            opacity: 0;
            cursor: nwse-resize;
            transition: opacity 0.2s;
        }
        .edit-panel:hover .resize-grip {
            opacity: 0.6;
        }
        .insert-btn {
            opacity: 0;
            transition: all 0.2s ease;
        }
        .grid-boundary:hover .insert-btn {
            opacity: 1;
        }
        .panel-active {
            outline: 1px solid #ea6d58 !important;
            background-color: rgba(255, 255, 255, 0.03) !important;
        }
    </style>
</head>
<body class="h-screen w-screen overflow-hidden flex bg-charcoal font-mono selection:bg-coral selection:text-charcoal" vid="11">

    <nav class="w-24 border-r border-white/10 flex flex-col justify-between items-center py-8 z-50 bg-charcoal shrink-0" vid="12">
        <div class="w-10 h-10 text-sage hover:text-coral transition-colors duration-300 cursor-pointer group" vid="13">
            <svg viewBox="0 0 100 100" fill="currentColor" vid="14">
                <rect x="10" y="10" width="35" height="80" class="group-hover:translate-y-[-5px] transition-transform duration-300" vid="15"></rect>
                <rect x="55" y="10" width="35" height="50" class="group-hover:translate-y-[5px] transition-transform duration-300" vid="16"></rect>
            </svg>
        </div>
        <div class="flex flex-col gap-12 items-center" vid="17">
            <button class="relative group" vid="18">
                <div class="text-white/40 transform -rotate-90 text-sm tracking-widest hover:text-white transition-colors" vid="19">PUBLIC</div>
            </button>
            <div class="w-[1px] h-12 bg-white/10" vid="20"></div>
            <button class="relative group" vid="21">
                <div class="text-white/40 transform -rotate-90 text-sm tracking-widest hover:text-white transition-colors" vid="22">SHARED</div>
            </button>
            <div class="w-[1px] h-12 bg-white/10" vid="23"></div>
            <button class="relative group" vid="24">
                <div class="text-coral transform -rotate-90 text-sm tracking-widest hover:text-white transition-colors" vid="25">PERSONAL</div>
            </button>
        </div>
        <div class="relative group cursor-pointer" vid="26">
            <div class="w-10 h-10 rounded-full border border-white/20 p-1 group-hover:border-coral transition-colors" vid="27">
                 <div class="w-full h-full rounded-full bg-cover bg-center grayscale group-hover:grayscale-0 transition-all" style="background-image: url('https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&amp;w=150&amp;auto=format&amp;fit=crop');" vid="28"></div>
            </div>
        </div>
    </nav>

    <main class="flex-1 flex flex-col h-full overflow-hidden relative" vid="29">
        <header class="h-20 border-b border-white/10 flex items-center justify-between px-12 bg-charcoal z-40 shrink-0" vid="30">
            <div class="flex items-center gap-4 text-xs tracking-widest uppercase text-white/50" vid="31">
                <a href="#" class="hover:text-coral transition-colors" vid="32">Back to Views</a>
                <span vid="33">/</span>
                <span class="text-coral" vid="34">Q4 Revenue Metrics</span>
                <span class="ml-4 px-2 py-0.5 bg-coral/10 text-coral text-[9px] border border-coral/20 rounded-sm" vid="35">EDITING</span>
            </div>
            
            <div class="flex items-center gap-4" vid="36">
                <button class="px-4 py-2 border border-white/10 text-[10px] tracking-[0.2em] uppercase text-white/60 hover:text-sage hover:border-sage transition-all" vid="37">Save Layout</button>
                <button class="px-4 py-2 border border-white/10 text-[10px] tracking-[0.2em] uppercase text-white/60 hover:text-sage hover:border-sage transition-all" vid="38">Discard</button>
                <div class="w-[1px] h-6 bg-white/10 mx-2" vid="39"></div>
                <label class="flex items-center gap-3 cursor-pointer group" vid="40">
                    <span class="text-[10px] tracking-[0.2em] uppercase text-coral transition-colors" vid="41">Edit Mode</span>
                    <div class="w-10 h-5 bg-coral/20 border border-coral/40 rounded-full relative" vid="42">
                        <div class="absolute right-1 top-1 w-2.5 h-2.5 bg-coral rounded-full transition-all" vid="43"></div>
                    </div>
                </label>
            </div>
        </header>

        <div class="flex-1 overflow-y-auto no-scrollbar scroll-smooth" vid="44">
            <section class="p-12 border-b border-white/10 edit-panel group" vid="45">
                <div class="drag-handle text-white/20 hover:text-coral" vid="46">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" vid="47"><path d="M5 9l7-7 7 7M5 15l7 7 7-7" vid="48"></path></svg>
                </div>
                <div class="flex flex-col md:flex-row md:items-end justify-between gap-6" vid="49">
                    <div vid="50">
                        <h1 class="text-8xl font-display text-sage uppercase leading-none mb-4" vid="51">Revenue Analysis</h1>
                        <p class="font-serif italic text-white/60 text-xl max-w-2xl" vid="52">Comprehensive tracking of donor pipeline and grant allocation for the final fiscal quarter of 2023.</p>
                    </div>
                    <div class="flex flex-col items-end" vid="53">
                        <div class="text-5xl font-display text-coral leading-none" vid="54">$4.2M</div>
                        <div class="text-[10px] tracking-widest text-white/40 mt-1 uppercase" vid="55">Total Quarterly Inflow</div>
                    </div>
                </div>
            </section>

            <div class="grid-boundary w-full flex justify-center py-2 relative group h-4 cursor-pointer" vid="56">
                <button class="insert-btn absolute -top-3 bg-charcoal border border-white/20 rounded-full p-1.5 hover:border-coral group/btn" vid="57">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" class="text-white/40 group-hover/btn:text-coral" vid="58"><path d="M12 5v14M5 12h14" vid="59"></path></svg>
                </button>
            </div>

            <section class="grid grid-cols-6 border-white/10" vid="60">
                
                <div class="col-span-1 border-r border-b border-white/10 p-8 flex flex-col justify-between edit-panel" vid="61">
                    <div class="drag-handle" vid="62"><svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" vid="63"><circle cx="9" cy="9" r="2" vid="64"></circle><circle cx="9" cy="15" r="2" vid="65"></circle><circle cx="15" cy="9" r="2" vid="66"></circle><circle cx="15" cy="15" r="2" vid="67"></circle></svg></div>
                    <div class="text-[10px] tracking-[0.2em] text-white/40 uppercase mb-4" vid="68">Conversion Rate</div>
                    <div class="text-4xl font-display text-sage" vid="69">18.4%</div>
                    <div class="mt-4 h-1 w-full bg-white/5 overflow-hidden" vid="70">
                        <div class="h-full bg-coral w-[18.4%]" vid="71"></div>
                    </div>
                    <div class="resize-grip" vid="72"><svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" vid="73"><path d="M21 15l-6 6M21 9L9 21" vid="74"></path></svg></div>
                </div>

                
                <div class="col-span-1 border-r border-b border-white/10 p-8 flex flex-col justify-between edit-panel" vid="75">
                    <div class="drag-handle" vid="76"><svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" vid="77"><circle cx="9" cy="9" r="2" vid="78"></circle><circle cx="9" cy="15" r="2" vid="79"></circle><circle cx="15" cy="9" r="2" vid="80"></circle><circle cx="15" cy="15" r="2" vid="81"></circle></svg></div>
                    <div class="text-[10px] tracking-[0.2em] text-white/40 uppercase mb-4" vid="82">Active Grants</div>
                    <div class="text-4xl font-display text-sage" vid="83">142</div>
                    <div class="text-[10px] text-coral mt-2" vid="84">↑ 12% vs last month</div>
                </div>

                
                <div class="col-span-1 border-r border-b border-white/10 p-8 flex flex-col justify-between edit-panel" vid="85">
                    <div class="drag-handle" vid="86"><svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" vid="87"><circle cx="9" cy="9" r="2" vid="88"></circle><circle cx="9" cy="15" r="2" vid="89"></circle><circle cx="15" cy="9" r="2" vid="90"></circle><circle cx="15" cy="15" r="2" vid="91"></circle></svg></div>
                    <div class="text-[10px] tracking-[0.2em] text-white/40 uppercase mb-4" vid="92">Avg Gift Size</div>
                    <div class="text-4xl font-display text-sage" vid="93">$12.5k</div>
                    <div class="text-[10px] text-white/20 mt-2" vid="94">Stabilized range</div>
                </div>

                
                <div class="col-span-1 border-r border-b border-white/10 p-8 flex flex-col justify-between edit-panel" vid="95">
                    <div class="drag-handle" vid="96"><svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" vid="97"><circle cx="9" cy="9" r="2" vid="98"></circle><circle cx="9" cy="15" r="2" vid="99"></circle><circle cx="15" cy="9" r="2" vid="100"></circle><circle cx="15" cy="15" r="2" vid="101"></circle></svg></div>
                    <div class="text-[10px] tracking-[0.2em] text-white/40 uppercase mb-4" vid="102">Burn Rate</div>
                    <div class="text-4xl font-display text-coral" vid="103">24%</div>
                    <div class="text-[10px] text-white/20 mt-2" vid="104">Within budget limits</div>
                </div>

                
                <div class="col-span-4 border-r border-b border-white/10 p-8 min-h-[400px] edit-panel panel-active" vid="105">
                    <div class="drag-handle opacity-60" vid="106"><svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" vid="107"><circle cx="9" cy="9" r="2" vid="108"></circle><circle cx="9" cy="15" r="2" vid="109"></circle><circle cx="15" cy="9" r="2" vid="110"></circle><circle cx="15" cy="15" r="2" vid="111"></circle></svg></div>
                    <div class="flex justify-between items-center mb-12" vid="112">
                        <div class="text-[10px] tracking-[0.2em] text-white/40 uppercase" vid="113">Revenue Over Time (USD)</div>
                        <div class="flex gap-4" vid="114">
                            <span class="text-[10px] text-sage flex items-center gap-2" vid="115"><span class="w-2 h-2 rounded-full bg-sage" vid="116"></span> Current</span>
                            <span class="text-[10px] text-white/20 flex items-center gap-2" vid="117"><span class="w-2 h-2 rounded-full bg-white/10" vid="118"></span> Previous</span>
                        </div>
                    </div>
                    <div class="h-64 flex items-end justify-between gap-4 relative" vid="119">
                        <div class="absolute inset-0 flex flex-col justify-between opacity-5" vid="120">
                            <div class="border-t border-white w-full" vid="121"></div>
                            <div class="border-t border-white w-full" vid="122"></div>
                            <div class="border-t border-white w-full" vid="123"></div>
                            <div class="border-t border-white w-full" vid="124"></div>
                        </div>
                        <div class="flex-1 bg-white/5 relative h-[40%]" vid="125"></div>
                        <div class="flex-1 bg-white/5 relative h-[65%]" vid="126"></div>
                        <div class="flex-1 bg-white/5 relative h-[55%]" vid="127"></div>
                        <div class="flex-1 bg-white/5 relative h-[80%]" vid="128"></div>
                        <div class="flex-1 bg-white/5 relative h-[95%]" vid="129"></div>
                        <div class="flex-1 bg-white/5 relative h-[70%]" vid="130"></div>
                        <div class="flex-1 bg-white/5 relative h-[85%]" vid="131"></div>
                    </div>
                    <div class="resize-grip opacity-60" vid="132"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" vid="133"><path d="M21 15l-6 6M21 9L9 21" vid="134"></path></svg></div>
                </div>

                
                <div class="col-span-2 border-r border-b border-white/10 p-8 flex flex-col edit-panel" vid="135">
                    <div class="drag-handle" vid="136"><svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" vid="137"><circle cx="9" cy="9" r="2" vid="138"></circle><circle cx="9" cy="15" r="2" vid="139"></circle><circle cx="15" cy="9" r="2" vid="140"></circle><circle cx="15" cy="15" r="2" vid="141"></circle></svg></div>
                    <div class="text-[10px] tracking-[0.2em] text-white/40 uppercase mb-8" vid="142">Donation Channels</div>
                    <div class="flex-1 flex items-center justify-center relative" vid="143">
                        <div class="w-48 h-48 rounded-full border-[16px] border-white/5 relative flex items-center justify-center" vid="144">
                            <div class="absolute inset-0 rounded-full border-[16px] border-coral border-t-transparent border-l-transparent rotate-45" vid="145"></div>
                            <div class="text-center" vid="146">
                                <div class="text-3xl font-display text-offwhite" vid="147">62%</div>
                                <div class="text-[8px] tracking-[0.2em] text-white/40 uppercase" vid="148">Direct</div>
                            </div>
                        </div>
                    </div>
                    <div class="resize-grip" vid="149"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" vid="150"><path d="M21 15l-6 6M21 9L9 21" vid="151"></path></svg></div>
                </div>

                
                <div class="col-span-6 grid-boundary flex items-center justify-center h-4 relative" vid="152">
                    <button class="insert-btn absolute -top-3 bg-charcoal border border-white/20 rounded-full p-1.5 hover:border-coral group/btn" vid="153">
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" class="text-white/40 group-hover/btn:text-coral" vid="154"><path d="M12 5v14M5 12h14" vid="155"></path></svg>
                    </button>
                </div>

                
                <div class="col-span-3 border-r border-b border-white/10 p-8 edit-panel" vid="156">
                    <div class="drag-handle" vid="157"><svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" vid="158"><circle cx="9" cy="9" r="2" vid="159"></circle><circle cx="9" cy="15" r="2" vid="160"></circle><circle cx="15" cy="9" r="2" vid="161"></circle><circle cx="15" cy="15" r="2" vid="162"></circle></svg></div>
                    <div class="text-[10px] tracking-[0.2em] text-white/40 uppercase mb-8" vid="163">Donor Pipeline Funnel</div>
                    <div class="space-y-4" vid="164">
                        <div class="relative h-12 bg-white/5 border-l-4 border-sage group overflow-hidden" vid="165">
                            <div class="absolute inset-0 bg-sage/5 w-full" vid="166"></div>
                            <div class="relative h-full flex items-center justify-between px-6" vid="167">
                                <span class="text-[11px] uppercase tracking-widest text-white/80" vid="168">Awareness / Leads</span>
                                <span class="font-display text-sage" vid="169">12,403</span>
                            </div>
                        </div>
                        <div class="relative h-12 bg-white/5 border-l-4 border-coral group overflow-hidden ml-12" vid="170">
                            <div class="absolute inset-0 bg-coral/10 w-[25%]" vid="171"></div>
                            <div class="relative h-full flex items-center justify-between px-6" vid="172">
                                <span class="text-[11px] uppercase tracking-widest text-coral" vid="173">Donation</span>
                                <span class="font-display text-coral" vid="174">2,281</span>
                            </div>
                        </div>
                    </div>
                    <div class="resize-grip" vid="175"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" vid="176"><path d="M21 15l-6 6M21 9L9 21" vid="177"></path></svg></div>
                </div>

                
                <div class="col-span-3 border-r border-b border-white/10 p-8 edit-panel" vid="178">
                    <div class="drag-handle" vid="179"><svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor" vid="180"><circle cx="9" cy="9" r="2" vid="181"></circle><circle cx="9" cy="15" r="2" vid="182"></circle><circle cx="15" cy="9" r="2" vid="183"></circle><circle cx="15" cy="15" r="2" vid="184"></circle></svg></div>
                    <div class="text-[10px] tracking-[0.2em] text-white/40 uppercase mb-8" vid="185">Allocation Velocity</div>
                    <div class="flex flex-col gap-6" vid="186">
                        <div class="flex items-center gap-8" vid="187">
                            <div class="w-16 text-[10px] text-white/20 uppercase" vid="188">Target</div>
                            <div class="flex-1 h-px bg-white/10 relative" vid="189">
                                <div class="absolute -top-1 left-[75%] w-2 h-2 bg-sage rotate-45" vid="190"></div>
                            </div>
                            <div class="w-12 text-right font-display text-sage" vid="191">75%</div>
                        </div>
                        <div class="flex items-center gap-8" vid="192">
                            <div class="w-16 text-[10px] text-white/20 uppercase" vid="193">Actual</div>
                            <div class="flex-1 h-px bg-white/10 relative" vid="194">
                                <div class="absolute -top-1 left-[58%] w-2 h-2 bg-coral rotate-45" vid="195"></div>
                            </div>
                            <div class="w-12 text-right font-display text-coral" vid="196">58%</div>
                        </div>
                    </div>
                    <div class="resize-grip" vid="197"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" vid="198"><path d="M21 15l-6 6M21 9L9 21" vid="199"></path></svg></div>
                </div>
            </section>

            <footer class="p-12 border-t border-white/10 text-white/20 text-xs flex flex-row justify-between items-center" vid="200">
                <div class="font-mono tracking-widest" vid="201">© 2023 DATA PLATFORM INC.</div>
                <div class="flex gap-8 tracking-wider" vid="202">
                    <span class="hover:text-white cursor-pointer transition-colors" vid="203">EXIT EDIT MODE</span>
                    <span class="flex items-center gap-2" vid="204">
                        <span class="w-1.5 h-1.5 rounded-full bg-coral animate-pulse" vid="205"></span>
                        SESSION: UNSAVED CHANGES
                    </span>
                </div>
            </footer>
        </div>
    </main>

    
    <div class="fixed bottom-12 right-12 bg-charcoal border border-coral/40 p-2 shadow-2xl flex flex-col gap-2 z-[100]" vid="206">
        <button class="w-10 h-10 flex items-center justify-center hover:bg-coral/10 text-coral" title="Add Chart" vid="207">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" vid="208"><path d="M12 5v14M5 12h14" vid="209"></path></svg>
        </button>
        <button class="w-10 h-10 flex items-center justify-center hover:bg-coral/10 text-white/40 hover:text-coral" title="Grid Settings" vid="210">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" vid="211"><rect x="3" y="3" width="18" height="18" rx="2" ry="2" vid="212"></rect><line x1="3" y1="9" x2="21" y2="9" vid="213"></line><line x1="3" y1="15" x2="21" y2="15" vid="214"></line><line x1="9" y1="3" x2="9" y2="21" vid="215"></line><line x1="15" y1="3" x2="15" y2="21" vid="216"></line></svg>
        </button>
        <button class="w-10 h-10 flex items-center justify-center hover:bg-coral/10 text-white/40 hover:text-coral" title="History" vid="217">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" vid="218"><path d="M1 4v6h6" vid="219"></path><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" vid="220"></path></svg>
        </button>
    </div>

</body></html>
```
