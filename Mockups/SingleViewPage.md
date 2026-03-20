The code below contains a design. This design should be used to create a new app or be added to an existing one.

Look at the current open project to determine if a project exists. If no project is open, create a new Vite project then create this view in React after componentizing it.

If a project does exist, determine the framework being used and implement the design within that framework. Identify whether reusable components already exist that can be used to implement the design faithfully and if so use them, otherwise create new components. If other views already exist in the project, make sure to place the view in a sensible route and connect it to the other views.

Ensure the visual characteristics, layout, and interactions in the design are preserved with perfect fidelity.

Run the dev command so the user can see the app once finished.

```html
<html lang="en" vid="0"><head vid="1">
    <meta charset="UTF-8" vid="2">
    <meta name="viewport" content="width=device-width, initial-scale=1.0" vid="3">
    <title vid="4">Q4 Revenue Metrics - Dashboard View</title>
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
        <header class="h-20 border-b border-white/10 flex items-center justify-between px-8 md:px-12 bg-charcoal z-40 shrink-0" vid="30">
            <div class="flex items-center gap-4 text-xs tracking-widest uppercase text-white/50" vid="31">
                <a href="#" class="hover:text-coral transition-colors" vid="32">Back to Views</a>
                <span vid="33">/</span>
                <span class="text-coral" vid="34">Q4 Revenue Metrics</span>
            </div>
            
            <div class="flex items-center gap-4" vid="35">
                <button class="px-4 py-2 border border-white/10 text-[10px] tracking-[0.2em] uppercase text-white/60 hover:text-sage hover:border-sage transition-all" vid="36">Share</button>
                <button class="px-4 py-2 border border-white/10 text-[10px] tracking-[0.2em] uppercase text-white/60 hover:text-sage hover:border-sage transition-all" vid="37">Comments (4)</button>
                <div class="w-[1px] h-6 bg-white/10 mx-2" vid="38"></div>
                <label class="flex items-center gap-3 cursor-pointer group" vid="39">
                    <span class="text-[10px] tracking-[0.2em] uppercase text-white/40 group-hover:text-coral transition-colors" vid="40">Edit Mode</span>
                    <div class="w-10 h-5 bg-white/5 border border-white/20 rounded-full relative" vid="41">
                        <div class="absolute left-1 top-1 w-2.5 h-2.5 bg-white/20 rounded-full transition-all" vid="42"></div>
                    </div>
                </label>
            </div>
        </header>

        <div class="flex-1 overflow-y-auto no-scrollbar scroll-smooth" vid="43">
            <section class="p-8 md:p-12 border-b border-white/10" vid="44">
                <div class="flex flex-col md:flex-row md:items-end justify-between gap-6" vid="45">
                    <div vid="46">
                        <h1 class="text-6xl md:text-8xl font-display text-sage uppercase leading-none mb-4" vid="47">Revenue Analysis</h1>
                        <p class="font-serif italic text-white/60 text-xl max-w-2xl" vid="48">Comprehensive tracking of donor pipeline and grant allocation for the final fiscal quarter of 2023.</p>
                    </div>
                    <div class="flex flex-col items-end" vid="49">
                        <div class="text-5xl font-display text-coral leading-none" vid="50">$4.2M</div>
                        <div class="text-[10px] tracking-widest text-white/40 mt-1 uppercase" vid="51">Total Quarterly Inflow</div>
                    </div>
                </div>
            </section>

            <section class="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-6 border-white/10" vid="52">
                <div class="md:col-span-1 border-r border-b border-white/10 p-8 flex flex-col justify-between" vid="53">
                    <div class="text-[10px] tracking-[0.2em] text-white/40 uppercase mb-4" vid="54">Conversion Rate</div>
                    <div class="text-4xl font-display text-sage" vid="55">18.4%</div>
                    <div class="mt-4 h-1 w-full bg-white/5 overflow-hidden" vid="56">
                        <div class="h-full bg-coral w-[18.4%]" vid="57"></div>
                    </div>
                </div>
                <div class="md:col-span-1 border-r border-b border-white/10 p-8 flex flex-col justify-between" vid="58">
                    <div class="text-[10px] tracking-[0.2em] text-white/40 uppercase mb-4" vid="59">Active Grants</div>
                    <div class="text-4xl font-display text-sage" vid="60">142</div>
                    <div class="text-[10px] text-coral mt-2" vid="61">↑ 12% vs last month</div>
                </div>
                <div class="md:col-span-1 border-r border-b border-white/10 p-8 flex flex-col justify-between" vid="62">
                    <div class="text-[10px] tracking-[0.2em] text-white/40 uppercase mb-4" vid="63">Avg Gift Size</div>
                    <div class="text-4xl font-display text-sage" vid="64">$12.5k</div>
                    <div class="text-[10px] text-white/20 mt-2" vid="65">Stabilized range</div>
                </div>
                <div class="md:col-span-1 border-r border-b border-white/10 p-8 flex flex-col justify-between" vid="66">
                    <div class="text-[10px] tracking-[0.2em] text-white/40 uppercase mb-4" vid="67">Burn Rate</div>
                    <div class="text-4xl font-display text-coral" vid="68">24%</div>
                    <div class="text-[10px] text-white/20 mt-2" vid="69">Within budget limits</div>
                </div>
                
                <div class="md:col-span-4 lg:col-span-4 border-r border-b border-white/10 p-8 min-h-[400px]" vid="70">
                    <div class="flex justify-between items-center mb-12" vid="71">
                        <div class="text-[10px] tracking-[0.2em] text-white/40 uppercase" vid="72">Revenue Over Time (USD)</div>
                        <div class="flex gap-4" vid="73">
                            <span class="text-[10px] text-sage flex items-center gap-2" vid="74"><span class="w-2 h-2 rounded-full bg-sage" vid="75"></span> Current</span>
                            <span class="text-[10px] text-white/20 flex items-center gap-2" vid="76"><span class="w-2 h-2 rounded-full bg-white/10" vid="77"></span> Previous</span>
                        </div>
                    </div>
                    <div class="h-64 flex items-end justify-between gap-4 relative" vid="78">
                        <div class="absolute inset-0 flex flex-col justify-between opacity-5" vid="79">
                            <div class="border-t border-white w-full" vid="80"></div>
                            <div class="border-t border-white w-full" vid="81"></div>
                            <div class="border-t border-white w-full" vid="82"></div>
                            <div class="border-t border-white w-full" vid="83"></div>
                        </div>
                        <div class="flex-1 bg-white/5 hover:bg-sage/20 transition-all group relative h-[40%]" vid="84"><div class="absolute bottom-0 w-full bg-sage h-0 group-hover:h-full transition-all duration-500 opacity-20" vid="85"></div></div>
                        <div class="flex-1 bg-white/5 hover:bg-sage/20 transition-all group relative h-[65%]" vid="86"></div>
                        <div class="flex-1 bg-white/5 hover:bg-sage/20 transition-all group relative h-[55%]" vid="87"></div>
                        <div class="flex-1 bg-white/5 hover:bg-sage/20 transition-all group relative h-[80%]" vid="88"></div>
                        <div class="flex-1 bg-white/5 hover:bg-sage/20 transition-all group relative h-[95%]" vid="89"></div>
                        <div class="flex-1 bg-white/5 hover:bg-sage/20 transition-all group relative h-[70%]" vid="90"></div>
                        <div class="flex-1 bg-white/5 hover:bg-sage/20 transition-all group relative h-[85%]" vid="91"></div>
                    </div>
                    <div class="flex justify-between mt-4 text-[10px] text-white/20 uppercase tracking-widest" vid="92">
                        <span vid="93">Oct 01</span>
                        <span vid="94">Oct 08</span>
                        <span vid="95">Oct 15</span>
                        <span vid="96">Oct 22</span>
                    </div>
                </div>

                <div class="md:col-span-2 lg:col-span-2 border-r border-b border-white/10 p-8 flex flex-col" vid="97">
                    <div class="text-[10px] tracking-[0.2em] text-white/40 uppercase mb-8" vid="98">Donation Channels</div>
                    <div class="flex-1 flex items-center justify-center relative" vid="99">
                        <div class="w-48 h-48 rounded-full border-[16px] border-white/5 relative flex items-center justify-center" vid="100">
                            <div class="absolute inset-0 rounded-full border-[16px] border-coral border-t-transparent border-l-transparent rotate-45" vid="101"></div>
                            <div class="text-center" vid="102">
                                <div class="text-3xl font-display text-offwhite" vid="103">62%</div>
                                <div class="text-[8px] tracking-[0.2em] text-white/40 uppercase" vid="104">Direct</div>
                            </div>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-4 mt-8" vid="105">
                        <div class="flex items-center gap-2" vid="106">
                            <div class="w-2 h-2 bg-coral" vid="107"></div>
                            <span class="text-[10px] text-white/60 uppercase" vid="108">Direct (62%)</span>
                        </div>
                        <div class="flex items-center gap-2" vid="109">
                            <div class="w-2 h-2 bg-sage" vid="110"></div>
                            <span class="text-[10px] text-white/60 uppercase" vid="111">Grants (24%)</span>
                        </div>
                        <div class="flex items-center gap-2" vid="112">
                            <div class="w-2 h-2 bg-white/20" vid="113"></div>
                            <span class="text-[10px] text-white/60 uppercase" vid="114">Other (14%)</span>
                        </div>
                    </div>
                </div>

                <div class="md:col-span-3 lg:col-span-3 border-r border-b border-white/10 p-8" vid="115">
                    <div class="text-[10px] tracking-[0.2em] text-white/40 uppercase mb-8" vid="116">Donor Pipeline Funnel</div>
                    <div class="space-y-4" vid="117">
                        <div class="relative h-12 bg-white/5 border-l-4 border-sage group overflow-hidden" vid="118">
                            <div class="absolute inset-0 bg-sage/5 w-full" vid="119"></div>
                            <div class="relative h-full flex items-center justify-between px-6" vid="120">
                                <span class="text-[11px] uppercase tracking-widest text-white/80" vid="121">Awareness / Leads</span>
                                <span class="font-display text-sage" vid="122">12,403</span>
                            </div>
                        </div>
                        <div class="relative h-12 bg-white/5 border-l-4 border-sage/60 group overflow-hidden ml-4" vid="123">
                            <div class="absolute inset-0 bg-sage/5 w-[65%]" vid="124"></div>
                            <div class="relative h-full flex items-center justify-between px-6" vid="125">
                                <span class="text-[11px] uppercase tracking-widest text-white/60" vid="126">Engagement</span>
                                <span class="font-display text-white/80" vid="127">8,102</span>
                            </div>
                        </div>
                        <div class="relative h-12 bg-white/5 border-l-4 border-coral/60 group overflow-hidden ml-8" vid="128">
                            <div class="absolute inset-0 bg-coral/5 w-[40%]" vid="129"></div>
                            <div class="relative h-full flex items-center justify-between px-6" vid="130">
                                <span class="text-[11px] uppercase tracking-widest text-white/60" vid="131">Intent</span>
                                <span class="font-display text-white/80" vid="132">3,490</span>
                            </div>
                        </div>
                        <div class="relative h-12 bg-white/5 border-l-4 border-coral group overflow-hidden ml-12" vid="133">
                            <div class="absolute inset-0 bg-coral/10 w-[25%]" vid="134"></div>
                            <div class="relative h-full flex items-center justify-between px-6" vid="135">
                                <span class="text-[11px] uppercase tracking-widest text-coral" vid="136">Donation</span>
                                <span class="font-display text-coral" vid="137">2,281</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="md:col-span-3 lg:col-span-3 border-r border-b border-white/10 p-8" vid="138">
                    <div class="text-[10px] tracking-[0.2em] text-white/40 uppercase mb-8" vid="139">Allocation Velocity</div>
                    <div class="flex flex-col gap-6" vid="140">
                        <div class="flex items-center gap-8" vid="141">
                            <div class="w-16 text-[10px] text-white/20 uppercase" vid="142">Target</div>
                            <div class="flex-1 h-px bg-white/10 relative" vid="143">
                                <div class="absolute -top-1 left-[75%] w-2 h-2 bg-sage rotate-45" vid="144"></div>
                            </div>
                            <div class="w-12 text-right font-display text-sage" vid="145">75%</div>
                        </div>
                        <div class="flex items-center gap-8" vid="146">
                            <div class="w-16 text-[10px] text-white/20 uppercase" vid="147">Actual</div>
                            <div class="flex-1 h-px bg-white/10 relative" vid="148">
                                <div class="absolute -top-1 left-[58%] w-2 h-2 bg-coral rotate-45" vid="149"></div>
                            </div>
                            <div class="w-12 text-right font-display text-coral" vid="150">58%</div>
                        </div>
                    </div>
                    <div class="mt-12 p-4 bg-white/[0.02] border border-white/5" vid="151">
                        <p class="text-[10px] text-white/40 font-serif italic" vid="152">"Allocation currently lagging due to delayed grant verification cycles in the Midwest region."</p>
                    </div>
                </div>
            </section>

            <footer class="p-12 border-t border-white/10 text-white/20 text-xs flex flex-col md:flex-row justify-between items-center gap-4" vid="153">
                <div class="font-mono tracking-widest" vid="154">© 2023 DATA PLATFORM INC.</div>
                <div class="flex gap-8 tracking-wider" vid="155">
                    <span class="hover:text-white cursor-pointer transition-colors" vid="156">PRIVACY</span>
                    <span class="hover:text-white cursor-pointer transition-colors" vid="157">TERMS</span>
                    <span class="flex items-center gap-2" vid="158">
                        <span class="w-1.5 h-1.5 rounded-full bg-sage" vid="159"></span>
                        STATUS: LIVE
                    </span>
                </div>
            </footer>
        </div>
    </main>

</body></html>
```
