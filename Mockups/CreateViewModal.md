The code below contains a design. This design should be used to create a new app or be added to an existing one.

Look at the current open project to determine if a project exists. If no project is open, create a new Vite project then create this view in React after componentizing it.

If a project does exist, determine the framework being used and implement the design within that framework. Identify whether reusable components already exist that can be used to implement the design faithfully and if so use them, otherwise create new components. If other views already exist in the project, make sure to place the view in a sensible route and connect it to the other views.

Ensure the visual characteristics, layout, and interactions in the design are preserved with perfect fidelity.

Run the dev command so the user can see the app once finished.

```html
<html lang="en" vid="0"><head vid="1">
    <meta charset="UTF-8" vid="2">
    <meta name="viewport" content="width=device-width, initial-scale=1.0" vid="3">
    <title vid="4">Data Platform - Views Variant</title>
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
        .vertical-text {
            writing-mode: vertical-rl;
            text-orientation: mixed;
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
        
        
        <header class="h-20 border-b border-white/10 flex items-center justify-between px-8 md:px-12 bg-charcoal z-40" vid="30">
            <div class="flex items-center gap-4 text-xs tracking-widest uppercase text-white/50" vid="31">
                <span class="text-coral" vid="32">System Admin</span>
                <span vid="33">/</span>
                <span vid="34">October 24, 2023</span>
            </div>
            
            <div class="flex items-center gap-6" vid="35">
                <div class="relative hidden md:block group" vid="36">
                    <input type="text" placeholder="SEARCH VIEWS..." class="bg-transparent border-b border-white/20 py-1 pr-8 text-sm focus:outline-none focus:border-sage placeholder-white/20 w-48 font-mono transition-colors" vid="37">
                    <svg class="w-4 h-4 text-white/40 absolute right-0 top-1 group-hover:text-sage transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" vid="38"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" vid="39"></path></svg>
                </div>

            </div>
        </header>

        
        <div class="flex-1 overflow-y-auto no-scrollbar relative scroll-smooth" vid="40">
            
            
            <section class="min-h-[35vh] flex flex-col justify-end px-8 md:px-12 pb-12 border-b border-white/10 relative overflow-hidden" vid="41">
                
                <div class="absolute top-0 right-20 w-[1px] h-full bg-white/5" vid="42"></div>
                <div class="absolute top-20 right-0 w-full h-[1px] bg-white/5" vid="43"></div>
                
                <div class="flex items-end justify-between relative z-10" vid="44">
                    <div vid="45">
                        <div class="flex items-center gap-3 mb-4" vid="46">
                            <div class="w-2 h-2 bg-coral rounded-full animate-pulse" vid="47"></div>
                            <h2 class="text-coral font-serif italic text-2xl md:text-3xl" vid="48">Welcome back, Administrator</h2>
                        </div>
                        <h1 class="text-[clamp(5rem,10vw,11rem)] leading-[0.8] font-display text-sage uppercase tracking-tight" vid="49">
                            My<br vid="50">Views
                        </h1>
                    </div>
                    <div class="hidden lg:block text-right mb-2" vid="51">
                        <div class="text-7xl font-display text-white/10 leading-none" vid="52">03</div>
                        <div class="text-xs tracking-widest text-white/40 mt-1 uppercase border-t border-white/10 pt-2" vid="53">Active Panels</div>
                    </div>
                </div>
            </section>

            
            <section class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 border-l border-white/10 auto-rows-fr" vid="54">
                
                
                <article class="group relative border-r border-b border-white/10 bg-charcoal hover:bg-[#161616] transition-all duration-500 flex flex-col min-h-[420px]" vid="55">
                    <div class="absolute top-0 right-0 p-6 opacity-50 group-hover:opacity-100 transition-opacity z-10" vid="56">
                        <div class="border border-white/20 rounded-full px-3 py-1 text-[10px] uppercase tracking-wider text-sage group-hover:border-sage group-hover:bg-sage/10 transition-colors" vid="57">
                            12 Panels
                        </div>
                    </div>
                    
                    <div class="flex-1 p-8 md:p-12 flex flex-col justify-center relative overflow-hidden" vid="58">
                         
                         <div class="absolute -left-4 top-20 text-[10rem] font-display text-white/[0.02] leading-none pointer-events-none select-none" vid="59">01</div>
                         
                         <div class="flex gap-4 mb-8 opacity-60 grayscale group-hover:grayscale-0 transition-all duration-500 relative z-10" vid="60">
                             <img src="https://upload.wikimedia.org/wikipedia/commons/4/4b/Stripe_Logo%2C_revised_2016.png" class="h-6 invert opacity-70 hover:opacity-100 transition-opacity" alt="Stripe" vid="61">
                             <img src="https://upload.wikimedia.org/wikipedia/commons/f/f9/Salesforce.com_logo.svg" class="h-6 invert opacity-70 hover:opacity-100 transition-opacity" alt="Salesforce" vid="62">
                         </div>
                        <h3 class="text-5xl md:text-6xl font-display uppercase leading-[0.85] text-offwhite group-hover:text-coral transition-colors duration-300 relative z-10" vid="63">
                            Q4 Revenue<br vid="64">Metrics
                        </h3>
                        <p class="font-serif italic text-white/60 mt-6 text-lg group-hover:text-white/80 transition-colors relative z-10 max-w-sm" vid="65">
                            Comprehensive tracking of donor pipeline and grant allocation.
                        </p>
                    </div>

                    <div class="px-8 md:px-12 py-6 border-t border-white/5 flex items-center justify-between mt-auto bg-black/20" vid="66">
                        <div class="flex items-center gap-4" vid="67">
                            <div class="w-10 h-10 rounded-full border border-sage p-0.5" vid="68">
                                <img src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100" class="w-full h-full rounded-full object-cover grayscale group-hover:grayscale-0 transition-all" vid="69">
                            </div>
                            <div vid="70">
                                <div class="text-sm font-bold text-offwhite font-mono" vid="71">Marcus Thorne</div>
                                <div class="text-[10px] uppercase tracking-widest text-coral" vid="72">Director of Finance</div>
                            </div>
                        </div>
                        <div class="opacity-0 group-hover:opacity-100 transition-opacity transform translate-x-[-10px] group-hover:translate-x-0 duration-300 bg-sage rounded-full p-2" vid="73">
                            <svg class="w-4 h-4 text-charcoal" fill="none" stroke="currentColor" viewBox="0 0 24 24" vid="74"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" vid="75"></path></svg>
                        </div>
                    </div>
                </article>

                
                <article class="group relative border-r border-b border-white/10 bg-charcoal hover:bg-[#161616] transition-all duration-500 flex flex-col min-h-[420px]" vid="76">
                    <div class="absolute top-0 right-0 p-6 opacity-50 group-hover:opacity-100 transition-opacity z-10" vid="77">
                        <div class="border border-white/20 rounded-full px-3 py-1 text-[10px] uppercase tracking-wider text-sage group-hover:border-sage group-hover:bg-sage/10 transition-colors" vid="78">
                            8 Panels
                        </div>
                    </div>
                    
                    <div class="flex-1 p-8 md:p-12 flex flex-col justify-center relative overflow-hidden" vid="79">
                        
                        <div class="absolute -left-4 top-20 text-[10rem] font-display text-white/[0.02] leading-none pointer-events-none select-none" vid="80">02</div>

                         <div class="flex gap-4 mb-8 opacity-60 grayscale group-hover:grayscale-0 transition-all duration-500 relative z-10" vid="81">
                             <img src="https://upload.wikimedia.org/wikipedia/commons/a/a7/Google_Analytics_Logo.svg" class="h-6 invert opacity-70 hover:opacity-100 transition-opacity" alt="GA" vid="82">
                             <img src="https://upload.wikimedia.org/wikipedia/commons/0/05/Facebook_Logo_%282019%29.png" class="h-6 invert opacity-70 hover:opacity-100 transition-opacity" alt="FB" vid="83">
                         </div>
                        <h3 class="text-5xl md:text-6xl font-display uppercase leading-[0.85] text-offwhite group-hover:text-coral transition-colors duration-300 relative z-10" vid="84">
                            User Flow<br vid="85">Analysis
                        </h3>
                        <p class="font-serif italic text-white/60 mt-6 text-lg group-hover:text-white/80 transition-colors relative z-10 max-w-sm" vid="86">
                            Mapping engagement across our volunteer portal.
                        </p>
                    </div>

                    <div class="px-8 md:px-12 py-6 border-t border-white/5 flex items-center justify-between mt-auto bg-black/20" vid="87">
                        <div class="flex items-center gap-4" vid="88">
                            <div class="w-10 h-10 rounded-full border border-sage p-0.5" vid="89">
                                <img src="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100" class="w-full h-full rounded-full object-cover grayscale group-hover:grayscale-0 transition-all" vid="90">
                            </div>
                            <div vid="91">
                                <div class="text-sm font-bold text-offwhite font-mono" vid="92">Sarah Jenkins</div>
                                <div class="text-[10px] uppercase tracking-widest text-coral" vid="93">Growth Lead</div>
                            </div>
                        </div>
                        <div class="opacity-0 group-hover:opacity-100 transition-opacity transform translate-x-[-10px] group-hover:translate-x-0 duration-300 bg-sage rounded-full p-2" vid="94">
                            <svg class="w-4 h-4 text-charcoal" fill="none" stroke="currentColor" viewBox="0 0 24 24" vid="95"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" vid="96"></path></svg>
                        </div>
                    </div>
                </article>

                
                <article class="group relative border-r border-b border-white/10 bg-charcoal hover:bg-[#161616] transition-all duration-500 flex flex-col min-h-[420px]" vid="97">
                    <div class="absolute top-0 right-0 p-6 opacity-50 group-hover:opacity-100 transition-opacity z-10" vid="98">
                        <div class="border border-white/20 rounded-full px-3 py-1 text-[10px] uppercase tracking-wider text-sage group-hover:border-sage group-hover:bg-sage/10 transition-colors" vid="99">
                            24 Panels
                        </div>
                    </div>
                    
                    <div class="flex-1 p-8 md:p-12 flex flex-col justify-center relative overflow-hidden" vid="100">
                        
                        <div class="absolute -left-4 top-20 text-[10rem] font-display text-white/[0.02] leading-none pointer-events-none select-none" vid="101">03</div>

                         <div class="flex gap-4 mb-8 opacity-60 grayscale group-hover:grayscale-0 transition-all duration-500 relative z-10" vid="102">
                             <img src="https://upload.wikimedia.org/wikipedia/commons/9/93/Amazon_Web_Services_Logo.svg" class="h-6 invert opacity-70 hover:opacity-100 transition-opacity" alt="AWS" vid="103">
                             <img src="https://upload.wikimedia.org/wikipedia/commons/3/39/Kubernetes_logo_without_workmark.svg" class="h-6 invert opacity-70 hover:opacity-100 transition-opacity" alt="K8s" vid="104">
                         </div>
                        <h3 class="text-5xl md:text-6xl font-display uppercase leading-[0.85] text-offwhite group-hover:text-coral transition-colors duration-300 relative z-10" vid="105">
                            Server<br vid="106">Health
                        </h3>
                        <p class="font-serif italic text-white/60 mt-6 text-lg group-hover:text-white/80 transition-colors relative z-10 max-w-sm" vid="107">
                            Infrastructure uptime for donation processing endpoints.
                        </p>
                    </div>

                    <div class="px-8 md:px-12 py-6 border-t border-white/5 flex items-center justify-between mt-auto bg-black/20" vid="108">
                        <div class="flex items-center gap-4" vid="109">
                            <div class="w-10 h-10 rounded-full border border-sage p-0.5" vid="110">
                                <img src="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100" class="w-full h-full rounded-full object-cover grayscale group-hover:grayscale-0 transition-all" vid="111">
                            </div>
                            <div vid="112">
                                <div class="text-sm font-bold text-offwhite font-mono" vid="113">Alex Chen</div>
                                <div class="text-[10px] uppercase tracking-widest text-coral" vid="114">Ops Manager</div>
                            </div>
                        </div>
                        <div class="opacity-0 group-hover:opacity-100 transition-opacity transform translate-x-[-10px] group-hover:translate-x-0 duration-300 bg-sage rounded-full p-2" vid="115">
                            <svg class="w-4 h-4 text-charcoal" fill="none" stroke="currentColor" viewBox="0 0 24 24" vid="116"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" vid="117"></path></svg>
                        </div>
                    </div>
                </article>

                 
                <article class="group relative border-r border-b border-white/10 bg-white/[0.02] hover:bg-white/5 transition-all duration-500 flex flex-col justify-center items-center min-h-[420px] cursor-pointer" vid="118">
                    <div class="w-24 h-24 rounded-full border border-dashed border-white/20 flex items-center justify-center group-hover:border-coral group-hover:scale-110 transition-all duration-300 bg-charcoal relative" vid="119">
                        <div class="absolute inset-0 bg-coral/20 rounded-full scale-0 group-hover:scale-100 transition-transform duration-300" vid="120"></div>
                        <svg class="w-8 h-8 text-white/40 group-hover:text-coral relative z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24" vid="121"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" vid="122"></path></svg>
                    </div>
                    <div class="mt-6 font-mono text-sm tracking-widest text-white/40 group-hover:text-coral uppercase transition-colors" vid="123">Create New View</div>
                    <p class="mt-2 text-white/20 text-xs font-serif italic text-center max-w-[200px]" vid="124">Add a custom dashboard based on your current metrics</p>
                </article>

                
                <article class="hidden lg:block border-r border-b border-white/10 bg-charcoal" vid="125"></article>
                <article class="hidden lg:block border-r border-b border-white/10 bg-charcoal" vid="126"></article>

            </section>
            
            
            <footer class="p-12 border-t border-white/10 text-white/20 text-xs flex flex-col md:flex-row justify-between items-center gap-4" vid="127">
                <div class="font-mono tracking-widest" vid="128">© 2023 DATA PLATFORM INC.</div>
                <div class="flex gap-8 tracking-wider" vid="129">
                    <span class="hover:text-white cursor-pointer transition-colors" vid="130">PRIVACY</span>
                    <span class="hover:text-white cursor-pointer transition-colors" vid="131">TERMS</span>
                    <span class="flex items-center gap-2" vid="132">
                        <span class="w-1.5 h-1.5 rounded-full bg-sage" vid="133"></span>
                        STATUS: OPERATIONAL
                    </span>
                </div>
            </footer>
        </div>
    </main>

  <!-- Create New View Modal -->
  <div class="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-sm" vid="134">
    <div class="relative bg-charcoal border border-white/10 w-full max-w-lg mx-4 overflow-hidden" vid="135">
      
      <!-- Corner accents -->
      <div class="absolute top-0 left-0 w-6 h-6 border-t border-l border-coral" vid="136"></div>
      <div class="absolute top-0 right-0 w-6 h-6 border-t border-r border-coral" vid="137"></div>
      <div class="absolute bottom-0 left-0 w-6 h-6 border-b border-l border-coral" vid="138"></div>
      <div class="absolute bottom-0 right-0 w-6 h-6 border-b border-r border-coral" vid="139"></div>

      <!-- Header -->
      <div class="px-10 pt-10 pb-6 border-b border-white/10 flex items-start justify-between" vid="140">
        <div vid="141">
          <p class="text-coral text-[10px] tracking-widest uppercase font-mono mb-2" vid="142">New View</p>
          <h2 class="font-display text-4xl uppercase text-offwhite leading-none" vid="143">Create<br vid="144">View</h2>
        </div>
        <button class="text-white/30 hover:text-coral transition-colors mt-1" vid="145">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" vid="146"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" vid="147"></path></svg>
        </button>
      </div>

      <!-- Form -->
      <div class="px-10 py-8 flex flex-col gap-8" vid="148">
        
        <!-- Name field -->
        <div class="group flex flex-col gap-2" vid="149">
          <label class="text-[10px] uppercase tracking-widest text-white/40 font-mono" vid="150">View Name</label>
          <div class="relative" vid="151">
            <input type="text" placeholder="e.g. Q4 Revenue Metrics" class="w-full bg-transparent border-b border-white/20 pb-2 text-offwhite font-mono text-sm placeholder-white/20 focus:outline-none focus:border-sage transition-colors" vid="152">
            <div class="absolute bottom-0 left-0 h-[1px] w-0 bg-coral group-focus-within:w-full transition-all duration-300" vid="153"></div>
          </div>
        </div>

        <!-- Description field -->
        <div class="group flex flex-col gap-2" vid="154">
          <label class="text-[10px] uppercase tracking-widest text-white/40 font-mono" vid="155">Description</label>
          <div class="relative" vid="156">
            <textarea rows="3" placeholder="A brief description of what this view tracks…" class="w-full bg-transparent border-b border-white/20 pb-2 text-offwhite font-mono text-sm placeholder-white/20 focus:outline-none focus:border-sage transition-colors resize-none" vid="157"></textarea>
            <div class="absolute bottom-0 left-0 h-[1px] w-0 bg-coral group-focus-within:w-full transition-all duration-300" vid="158"></div>
          </div>
        </div>

      </div>

      <!-- Footer -->
      <div class="px-10 pb-10 flex items-center justify-between" vid="159">
        <button class="text-white/30 hover:text-white text-xs tracking-widest uppercase font-mono transition-colors" vid="160">Cancel</button>
        <button class="group flex items-center gap-3 bg-coral hover:bg-sage text-charcoal font-mono text-xs uppercase tracking-widest px-6 py-3 transition-colors duration-300" vid="161">
          <span vid="162">Create View</span>
          <svg class="w-4 h-4 transform group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24" vid="163"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" vid="164"></path></svg>
        </button>
      </div>

    </div>
  </div>

  <!-- Create New View Modal -->
  <div class="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-sm" vid="165">
    <div class="relative bg-charcoal border border-white/10 w-full max-w-lg mx-4 overflow-hidden" vid="166">
      
      <!-- Corner accents -->
      <div class="absolute top-0 left-0 w-6 h-6 border-t border-l border-coral" vid="167"></div>
      <div class="absolute top-0 right-0 w-6 h-6 border-t border-r border-coral" vid="168"></div>
      <div class="absolute bottom-0 left-0 w-6 h-6 border-b border-l border-coral" vid="169"></div>
      <div class="absolute bottom-0 right-0 w-6 h-6 border-b border-r border-coral" vid="170"></div>

      <!-- Header -->
      <div class="px-10 pt-10 pb-6 border-b border-white/10 flex items-start justify-between" vid="171">
        <div vid="172">
          <p class="text-coral text-[10px] tracking-widest uppercase font-mono mb-2" vid="173">New View</p>
          <h2 class="font-display text-4xl uppercase text-offwhite leading-none" vid="174">Create<br vid="175">View</h2>
        </div>
        <button class="text-white/30 hover:text-coral transition-colors mt-1" vid="176">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" vid="177"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" vid="178"></path></svg>
        </button>
      </div>

      <!-- Form -->
      <div class="px-10 py-8 flex flex-col gap-8" vid="179">
        
        <!-- Name field -->
        <div class="group flex flex-col gap-2" vid="180">
          <label class="text-[10px] uppercase tracking-widest text-white/40 font-mono" vid="181">View Name</label>
          <div class="relative" vid="182">
            <input type="text" placeholder="e.g. Q4 Revenue Metrics" class="w-full bg-transparent border-b border-white/20 pb-2 text-offwhite font-mono text-sm placeholder-white/20 focus:outline-none focus:border-sage transition-colors" vid="183">
            <div class="absolute bottom-0 left-0 h-[1px] w-0 bg-coral group-focus-within:w-full transition-all duration-300" vid="184"></div>
          </div>
        </div>

        <!-- Description field -->
        <div class="group flex flex-col gap-2" vid="185">
          <label class="text-[10px] uppercase tracking-widest text-white/40 font-mono" vid="186">Description</label>
          <div class="relative" vid="187">
            <textarea rows="3" placeholder="A brief description of what this view tracks…" class="w-full bg-transparent border-b border-white/20 pb-2 text-offwhite font-mono text-sm placeholder-white/20 focus:outline-none focus:border-sage transition-colors resize-none" vid="188"></textarea>
            <div class="absolute bottom-0 left-0 h-[1px] w-0 bg-coral group-focus-within:w-full transition-all duration-300" vid="189"></div>
          </div>
        </div>

      </div>

      <!-- Footer -->
      <div class="px-10 pb-10 flex items-center justify-between" vid="190">
        <button class="text-white/30 hover:text-white text-xs tracking-widest uppercase font-mono transition-colors" vid="191">Cancel</button>
        <button class="group flex items-center gap-3 bg-coral hover:bg-sage text-charcoal font-mono text-xs uppercase tracking-widest px-6 py-3 transition-colors duration-300" vid="192">
          <span vid="193">Create View</span>
          <svg class="w-4 h-4 transform group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24" vid="194"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" vid="195"></path></svg>
        </button>
      </div>

    </div>
  </div>

</body></html>
```
