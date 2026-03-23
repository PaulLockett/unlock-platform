The code below contains a design. This design should be used to create a new app or be added to an existing one.

Look at the current open project to determine if a project exists. If no project is open, create a new Vite project then create this view in React after componentizing it.

If a project does exist, determine the framework being used and implement the design within that framework. Identify whether reusable components already exist that can be used to implement the design faithfully and if so use them, otherwise create new components. If other views already exist in the project, make sure to place the view in a sensible route and connect it to the other views.

Ensure the visual characteristics, layout, and interactions in the design are preserved with perfect fidelity.

Run the dev command so the user can see the app once finished.

```html
<html lang="en" vid="0"><head vid="1">
    <meta charset="UTF-8" vid="2">
    <meta name="viewport" content="width=device-width, initial-scale=1.0" vid="3">
    <title vid="4">Server Health Dashboard - Data Platform</title>
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
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
        .chart-grid {
            background-image: radial-gradient(rgba(255,255,255,0.05) 1px, transparent 1px);
            background-size: 30px 30px;
        }
    </style>
</head>
<body class="h-screen w-screen overflow-hidden flex bg-charcoal font-mono selection:bg-coral selection:text-charcoal" vid="11">

    <nav class="w-20 md:w-24 border-r border-white/10 flex flex-col justify-between items-center py-8 z-50 bg-charcoal shrink-0" vid="12">
        <div class="w-10 h-10 text-sage hover:text-coral transition-colors duration-300 cursor-pointer group" vid="13">
            <svg viewBox="0 0 100 100" fill="currentColor" vid="14">
                <rect x="10" y="10" width="35" height="80" class="group-hover:translate-y-[-5px] transition-transform duration-300" vid="15"></rect>
                <rect x="55" y="10" width="35" height="50" class="group-hover:translate-y-[5px] transition-transform duration-300" vid="16"></rect>
            </svg>
        </div>
        <div class="flex flex-col gap-12 items-center" vid="17">
            <button class="relative group" vid="18"><div class="text-white/40 transform -rotate-90 text-sm tracking-widest hover:text-white transition-colors" vid="19">PUBLIC</div></button>
            <div class="w-[1px] h-12 bg-white/10" vid="20"></div>
            <button class="relative group" vid="21"><div class="text-white/40 transform -rotate-90 text-sm tracking-widest hover:text-white transition-colors" vid="22">SHARED</div></button>
            <div class="w-[1px] h-12 bg-white/10" vid="23"></div>
            <button class="relative group" vid="24"><div class="text-coral transform -rotate-90 text-sm tracking-widest hover:text-white transition-colors" vid="25">PERSONAL</div></button>
        </div>
        <div class="w-10 h-10 rounded-full border border-white/20 p-1 group cursor-pointer" vid="26">
             <div class="w-full h-full rounded-full bg-cover bg-center grayscale" style="background-image: url('https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&amp;w=150&amp;auto=format&amp;fit=crop');" vid="27"></div>
        </div>
    </nav>

    <main class="flex-1 flex flex-col h-full overflow-hidden relative" vid="28">
        <header class="h-20 border-b border-white/10 flex items-center justify-between px-8 md:px-12 bg-charcoal z-40" vid="29">
            <div class="flex items-center gap-4 text-xs tracking-widest uppercase text-white/50" vid="30">
                <span class="text-coral" vid="31">Personal Views</span>
                <span vid="32">/</span>
                <span vid="33">Server Health</span>
            </div>
            <div class="flex items-center gap-4" vid="34">
                <button class="px-4 py-2 border border-white/10 text-[10px] tracking-[0.2em] uppercase hover:bg-white/5 transition-colors" vid="35">Share</button>
                <button class="px-4 py-2 border border-white/10 text-[10px] tracking-[0.2em] uppercase hover:bg-white/5 transition-colors" vid="36">Comment</button>
                <div class="h-8 w-[1px] bg-white/10 mx-2" vid="37"></div>
                <div class="flex items-center gap-3" vid="38">
                    <span class="text-[10px] tracking-widest text-white/40" vid="39">EDIT MODE</span>
                    <div class="w-10 h-5 bg-white/10 rounded-full relative cursor-pointer" vid="40">
                        <div class="absolute left-1 top-1 w-3 h-3 bg-sage rounded-full" vid="41"></div>
                    </div>
                </div>
            </div>
        </header>

        <div class="flex-1 overflow-y-auto no-scrollbar chart-grid" vid="42">
            <section class="px-8 md:px-12 py-12 border-b border-white/10" vid="43">
                <h1 class="text-7xl md:text-8xl font-display text-sage uppercase leading-none tracking-tighter mb-4" vid="44">Server Health</h1>
                <p class="font-serif italic text-white/40 text-xl max-w-2xl" vid="45">Infrastructure uptime for donation processing endpoints. Monitoring real-time latency and throughput.</p>
            </section>

            <div class="grid grid-cols-1 md:grid-cols-4 border-b border-white/10" vid="46">
                <div class="p-8 border-r border-white/10" vid="47">
                    <div class="text-[10px] tracking-[0.3em] uppercase text-white/30 mb-2" vid="48">Global Uptime</div>
                    <div class="text-5xl font-display text-sage" vid="49">99.98%</div>
                    <div class="mt-4 flex items-center gap-2 text-[10px] text-sage/60" vid="50">
                        <span class="w-2 h-2 rounded-full bg-sage" vid="51"></span> OPERATIONAL
                    </div>
                </div>
                <div class="p-8 border-r border-white/10" vid="52">
                    <div class="text-[10px] tracking-[0.3em] uppercase text-white/30 mb-2" vid="53">Avg Latency</div>
                    <div class="text-5xl font-display text-offwhite" vid="54">124<span class="text-xl ml-1" vid="55">ms</span></div>
                    <div class="mt-4 text-[10px] text-coral uppercase tracking-widest" vid="56">↑ 12ms from prev</div>
                </div>
                <div class="p-8 border-r border-white/10" vid="57">
                    <div class="text-[10px] tracking-[0.3em] uppercase text-white/30 mb-2" vid="58">Request Vol</div>
                    <div class="text-5xl font-display text-offwhite" vid="59">2.4<span class="text-xl ml-1" vid="60">M</span></div>
                    <div class="mt-4 text-[10px] text-sage uppercase tracking-widest" vid="61">Last 24 Hours</div>
                </div>
                <div class="p-8" vid="62">
                    <div class="text-[10px] tracking-[0.3em] uppercase text-white/30 mb-2" vid="63">Active Nodes</div>
                    <div class="text-5xl font-display text-offwhite" vid="64">142</div>
                    <div class="mt-4 text-[10px] text-white/20 uppercase tracking-widest" vid="65">Cluster: US-East-1</div>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 border-b border-white/10" vid="66">
                <div class="lg:col-span-2 p-8 md:p-12 border-r border-white/10" vid="67">
                    <div class="flex justify-between items-center mb-12" vid="68">
                        <h3 class="text-xs tracking-[0.4em] uppercase text-white/50" vid="69">Server Load Over Time (7D)</h3>
                        <div class="flex gap-4 text-[10px] tracking-widest" vid="70">
                            <span class="text-sage" vid="71">● CPU</span>
                            <span class="text-coral" vid="72">● MEMORY</span>
                        </div>
                    </div>
                    <div class="h-64 w-full relative" vid="73">
                        <svg class="w-full h-full" preserveAspectRatio="none" viewBox="0 0 1000 100" vid="74">
                            <path d="M0 80 Q 100 20, 200 70 T 400 40 T 600 80 T 800 30 T 1000 60" fill="none" stroke="#dbe4d0" stroke-width="2" vid="75"></path>
                            <path d="M0 90 Q 150 40, 300 85 T 600 50 T 900 95 T 1000 70" fill="none" stroke="#ea6d58" stroke-width="2" opacity="0.5" vid="76"></path>
                            <line x1="0" y1="100" x2="1000" y2="100" stroke="white" stroke-opacity="0.1" vid="77"></line>
                        </svg>
                        <div class="absolute bottom-0 left-0 w-full flex justify-between text-[10px] text-white/20 mt-4 uppercase tracking-tighter pt-4" vid="78">
                            <span vid="79">Mon</span><span vid="80">Tue</span><span vid="81">Wed</span><span vid="82">Thu</span><span vid="83">Fri</span><span vid="84">Sat</span><span vid="85">Sun</span>
                        </div>
                    </div>
                </div>
                <div class="p-8 md:p-12 flex flex-col" vid="86">
                    <h3 class="text-xs tracking-[0.4em] uppercase text-white/50 mb-12" vid="87">Status Distribution</h3>
                    <div class="flex-1 flex items-center justify-center relative" vid="88">
                        <div class="w-48 h-48 rounded-full border-[20px] border-sage border-r-coral border-b-white/10" vid="89"></div>
                        <div class="absolute text-center" vid="90">
                            <div class="text-2xl font-display text-offwhite" vid="91">HTTP</div>
                            <div class="text-[10px] text-white/40 tracking-widest" vid="92">CODES</div>
                        </div>
                    </div>
                    <div class="mt-8 space-y-2" vid="93">
                        <div class="flex justify-between text-[10px] tracking-widest uppercase" vid="94">
                            <span class="text-sage" vid="95">200 OK</span><span vid="96">84%</span>
                        </div>
                        <div class="flex justify-between text-[10px] tracking-widest uppercase" vid="97">
                            <span class="text-coral" vid="98">404/500</span><span vid="99">12%</span>
                        </div>
                        <div class="flex justify-between text-[10px] tracking-widest uppercase" vid="100">
                            <span class="text-white/20" vid="101">Other</span><span vid="102">4%</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-2" vid="103">
                <div class="p-8 md:p-12 border-r border-white/10 border-b border-white/10 lg:border-b-0" vid="104">
                    <h3 class="text-xs tracking-[0.4em] uppercase text-white/50 mb-12" vid="105">Request Volume (Hourly)</h3>
                    <div class="flex items-end gap-2 h-48" vid="106">
                        <div class="flex-1 bg-white/5 h-[30%]" vid="107"></div>
                        <div class="flex-1 bg-white/5 h-[45%]" vid="108"></div>
                        <div class="flex-1 bg-sage h-[85%]" vid="109"></div>
                        <div class="flex-1 bg-sage h-[100%]" vid="110"></div>
                        <div class="flex-1 bg-white/5 h-[60%]" vid="111"></div>
                        <div class="flex-1 bg-white/5 h-[40%]" vid="112"></div>
                        <div class="flex-1 bg-coral h-[20%]" vid="113"></div>
                        <div class="flex-1 bg-white/5 h-[35%]" vid="114"></div>
                    </div>
                    <div class="flex justify-between text-[10px] text-white/20 mt-4 tracking-widest uppercase" vid="115">
                        <span vid="116">00:00</span><span vid="117">Peak</span><span vid="118">Current</span>
                    </div>
                </div>
                <div class="p-8 md:p-12" vid="119">
                    <h3 class="text-xs tracking-[0.4em] uppercase text-white/50 mb-12" vid="120">Error Resolution Flow</h3>
                    <div class="space-y-4" vid="121">
                        <div class="flex items-center" vid="122">
                            <div class="w-full h-8 bg-white/10 flex items-center px-4 justify-between" vid="123">
                                <span class="text-[10px] tracking-widest" vid="124">DETECTED</span>
                                <span class="text-[10px]" vid="125">1,240</span>
                            </div>
                        </div>
                        <div class="flex items-center justify-center" vid="126">
                            <div class="w-[80%] h-8 bg-white/5 border-l border-coral flex items-center px-4 justify-between" vid="127">
                                <span class="text-[10px] tracking-widest" vid="128">TRIAGED</span>
                                <span class="text-[10px]" vid="129">980</span>
                            </div>
                        </div>
                        <div class="flex items-center justify-center" vid="130">
                            <div class="w-[50%] h-8 bg-coral/20 border-l-2 border-coral flex items-center px-4 justify-between" vid="131">
                                <span class="text-[10px] tracking-widest text-coral" vid="132">RESOLVED</span>
                                <span class="text-[10px] text-coral font-bold" vid="133">620</span>
                            </div>
                        </div>
                    </div>
                    <p class="mt-8 font-serif italic text-white/30 text-sm" vid="134">MTTR currently at 42 mins. Alerting latency in Segment B.</p>
                </div>
            </div>

            <footer class="p-12 border-t border-white/10 text-white/20 text-xs flex justify-between items-center" vid="135">
                <div class="font-mono tracking-widest" vid="136">© 2023 INFRA-MONITOR</div>
                <div class="flex gap-8 tracking-wider" vid="137">
                    <span class="flex items-center gap-2" vid="138">
                        <span class="w-1.5 h-1.5 rounded-full bg-sage" vid="139"></span>
                        ALL SYSTEMS GO
                    </span>
                </div>
            </footer>
        </div>
    </main>


</body></html>
```
