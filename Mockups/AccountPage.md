The code below contains a design. This design should be used to create a new app or be added to an existing one.

Look at the current open project to determine if a project exists. If no project is open, create a new Vite project then create this view in React after componentizing it.

If a project does exist, determine the framework being used and implement the design within that framework. Identify whether reusable components already exist that can be used to implement the design faithfully and if so use them, otherwise create new components. If other views already exist in the project, make sure to place the view in a sensible route and connect it to the other views.

Ensure the visual characteristics, layout, and interactions in the design are preserved with perfect fidelity.

Run the dev command so the user can see the app once finished.

```html
<html lang="en" vid="0"><head vid="1">
    <meta charset="UTF-8" vid="2">
    <meta name="viewport" content="width=device-width, initial-scale=1.0" vid="3">
    <title vid="4">Account Settings - Data Platform</title>
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
        .custom-checkbox:checked + div { background-color: #ea6d58; border-color: #ea6d58; }
        .custom-checkbox:checked + div svg { opacity: 1; }
    </style>
</head>
<body class="h-screen w-screen overflow-hidden flex bg-charcoal font-mono selection:bg-coral selection:text-charcoal" vid="11">

    <nav class="w-20 md:w-24 border-r border-white/10 flex flex-col justify-between items-center py-8 z-50 bg-charcoal shrink-0" vid="12">
        <div class="w-10 h-10 text-sage hover:text-coral transition-colors duration-300 cursor-pointer group" onclick="window.location.reload()" vid="13">
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
                <div class="text-white/40 transform -rotate-90 text-sm tracking-widest hover:text-white transition-colors" vid="25">PERSONAL</div>
            </button>
        </div>

        <div class="relative group cursor-pointer" vid="26">
            <div class="w-10 h-10 rounded-full border border-coral p-1 transition-colors" vid="27">
                 <div class="w-full h-full rounded-full bg-cover bg-center" style="background-image: url('https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&amp;w=150&amp;auto=format&amp;fit=crop');" vid="28"></div>
            </div>

        </div>
    </nav>

    <main class="flex-1 flex flex-col h-full overflow-hidden relative" vid="29">
        <header class="h-20 border-b border-white/10 flex items-center justify-between px-8 md:px-12 bg-charcoal z-40" vid="30">
            <div class="flex items-center gap-4 text-xs tracking-widest uppercase text-white/50" vid="31">
                <span class="text-white/30" vid="32">System Admin</span>
                <span vid="33">/</span>
                <span class="text-coral" vid="34">Settings &amp; Profile</span>
            </div>
        </header>

        <div class="flex-1 overflow-y-auto no-scrollbar relative scroll-smooth bg-[#0d0d0d]" vid="35">
            
            <section class="px-8 md:px-12 py-16 border-b border-white/10" vid="36">
                <div class="max-w-6xl mx-auto flex flex-col md:flex-row gap-16 items-start" vid="37">
                    <div class="w-full md:w-1/3" vid="38">
                        <div class="sticky top-12" vid="39">
                            <h1 class="text-7xl font-display text-sage uppercase leading-[0.8] mb-6" vid="40">Account<br vid="41">Profile</h1>
                            <p class="font-serif italic text-white/40 text-lg leading-relaxed" vid="42">Manage your administrative credentials and visual preferences across the platform.</p>
                        </div>
                    </div>
                    
                    <div class="flex-1 space-y-20" vid="43">
                        
                        <div vid="44">
                            <h3 class="text-xs tracking-[0.3em] text-coral uppercase mb-10 pb-2 border-b border-white/5" vid="45">01 / Personal Details</h3>
                            
                            <div class="flex items-end gap-8 mb-12" vid="46">
                                <div class="relative group/avatar" vid="47">
                                    <div class="w-24 h-24 rounded-full border border-white/10 bg-cover bg-center overflow-hidden" style="background-image: url('https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&amp;w=300&amp;auto=format&amp;fit=crop');" vid="48"></div>
                                    <label class="absolute inset-0 rounded-full flex items-center justify-center bg-charcoal/70 opacity-0 group-hover/avatar:opacity-100 transition-opacity cursor-pointer" vid="49">
                                        <input type="file" accept="image/*" class="hidden" vid="50">
                                        <svg class="w-5 h-5 text-coral" fill="none" stroke="currentColor" viewBox="0 0 24 24" vid="51"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" vid="52"></path><circle cx="12" cy="13" r="3" vid="53"></circle></svg>
                                    </label>
                                </div>
                                <div vid="54">
                                    <div class="text-[10px] text-white/30 uppercase tracking-widest mb-2" vid="55">Profile Photo</div>
                                    <label class="text-[10px] tracking-widest text-coral border border-coral/30 px-4 py-1.5 hover:bg-coral hover:text-charcoal transition-all uppercase cursor-pointer" vid="56">
                                        <input type="file" accept="image/*" class="hidden" vid="57">Upload New Photo
                                    </label>
                                    <p class="mt-2 text-[10px] text-white/20 font-mono" vid="58">JPG, PNG or GIF · max 2MB</p>
                                </div>
                            </div>

                            <div class="grid grid-cols-1 md:grid-cols-2 gap-8" vid="59">
                                <div class="space-y-2" vid="60">
                                    <label class="text-[10px] text-white/30 uppercase tracking-widest" vid="61">Full Name</label>
                                    <input type="text" value="Administrator" class="w-full bg-transparent border-b border-white/10 py-2 text-xl font-serif italic text-offwhite focus:outline-none focus:border-coral transition-colors" vid="62">
                                </div>
                                <div class="space-y-2" vid="63">
                                    <label class="text-[10px] text-white/30 uppercase tracking-widest" vid="64">Email Address</label>
                                    <input type="email" value="admin@dataplatform.io" class="w-full bg-transparent border-b border-white/10 py-2 text-xl font-mono text-offwhite focus:outline-none focus:border-coral transition-colors" vid="65">
                                </div>
                                <div class="space-y-2 md:col-span-2" vid="66">
                                    <label class="text-[10px] text-white/30 uppercase tracking-widest" vid="67">Bio / Designation</label>
                                    <input type="text" value="System Administrator &amp; Infrastructure Lead" class="w-full bg-transparent border-b border-white/10 py-2 text-xl font-serif italic text-offwhite focus:outline-none focus:border-coral transition-colors" vid="68">
                                </div>
                            </div>
                        </div>

                        


                        
                        <div vid="69">
                            <h3 class="text-xs tracking-[0.3em] text-coral uppercase mb-10 pb-2 border-b border-white/5" vid="70">02 / Platform Experience</h3>
                            <div class="grid grid-cols-1 gap-12" vid="71">
                                <div class="space-y-6" vid="72">
                                    <div class="text-[10px] text-white/30 uppercase tracking-widest mb-4" vid="73">Theme Configuration</div>
                                    <div class="flex gap-4" vid="74">
                                        <button class="w-10 h-10 rounded-full bg-charcoal border-2 border-coral flex items-center justify-center shadow-lg" vid="75">
                                            <div class="w-4 h-4 rounded-full bg-coral" vid="76"></div>
                                        </button>
                                        <button class="w-10 h-10 rounded-full bg-[#f5f5f1] border border-white/10" vid="77"></button>
                                        <button class="w-10 h-10 rounded-full bg-[#1a2b25] border border-white/10" vid="78"></button>
                                    </div>
                                    <div class="pt-4" vid="79">
                                        <div class="flex items-center gap-3 group cursor-pointer w-fit" vid="80">
                                            <span class="text-sm text-white/60 group-hover:text-offwhite transition-colors" vid="81">High Contrast Mode</span>
                                            <div class="w-10 h-5 bg-white/10 rounded-full relative transition-colors" vid="82">
                                                <div class="absolute top-1 left-1 w-3 h-3 bg-white/40 rounded-full" vid="83"></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                            </div>
                        </div>

                    </div>
                </div>
            </section>

            <!-- Save Bar -->
            <div id="save-bar" class="px-8 md:px-12 py-5 flex items-center justify-between transition-all duration-500 opacity-0 pointer-events-none" style="background: #1e1008; border-top: 1px solid rgba(234,109,88,0.35); border-bottom: 1px solid rgba(234,109,88,0.15); box-shadow: 0 -4px 24px rgba(234,109,88,0.12);" vid="84">
                <div class="flex items-center gap-3 text-xs text-white/40 tracking-widest" vid="85">
                    <span class="w-1.5 h-1.5 rounded-full bg-coral animate-pulse" vid="86"></span>
                    <span id="edit-count" vid="87">UNSAVED CHANGES</span>
                </div>
                <div class="flex items-center gap-4" vid="88">
                    <button onclick="discardChanges()" class="text-[10px] tracking-[0.2em] text-white/30 hover:text-white/60 transition-colors uppercase" vid="89">Discard</button>
                    <button onclick="saveChanges()" class="text-[10px] tracking-[0.2em] text-sage border border-sage/30 px-6 py-2 hover:bg-sage hover:text-charcoal transition-all uppercase" vid="90">Save Changes</button>
                </div>
            </div>

            <footer class="p-12 border-t border-white/10 text-white/20 text-xs flex flex-col md:flex-row justify-between items-center gap-4" vid="91">
                <div class="font-mono tracking-widest" vid="92">© 2023 DATA PLATFORM INC.</div>
                <div class="flex items-center gap-2 text-coral tracking-wider" vid="93">
                    <span class="w-1.5 h-1.5 rounded-full bg-coral animate-pulse" vid="94"></span>
                    SYSTEM OPERATIONAL
                </div>
            </footer>
        </div>
    </main>

<script vid="95">
    const fields = document.querySelectorAll('input[type="text"], input[type="email"]');
    const saveBar = document.getElementById('save-bar');
    const originalValues = {};
    let dirtyFields = new Set();

    fields.forEach(input => {
        originalValues[input.name || input.type + input.value] = input.value;
        const key = input;
        input.addEventListener('input', () => {
            const orig = originalValues[input.name || input.type + Object.keys(originalValues).find(k => k.includes(input.type))];
            if (input.value !== input.defaultValue) {
                dirtyFields.add(input);
                input.classList.add('border-coral', 'text-coral');
                input.classList.remove('border-white/10');
            } else {
                dirtyFields.delete(input);
                input.classList.remove('border-coral', 'text-coral');
                input.classList.add('border-white/10');
            }
            updateSaveBar();
        });
    });

    function updateSaveBar() {
        if (dirtyFields.size > 0) {
            saveBar.classList.remove('opacity-0', 'pointer-events-none');
            saveBar.classList.add('opacity-100');
        } else {
            saveBar.classList.add('opacity-0', 'pointer-events-none');
            saveBar.classList.remove('opacity-100');
        }
    }

    function saveChanges() {
        fields.forEach(input => {
            input.defaultValue = input.value;
            input.classList.remove('border-coral', 'text-coral');
            input.classList.add('border-white/10');
        });
        dirtyFields.clear();
        updateSaveBar();
    }

    function discardChanges() {
        fields.forEach(input => {
            input.value = input.defaultValue;
            input.classList.remove('border-coral', 'text-coral');
            input.classList.add('border-white/10');
        });
        dirtyFields.clear();
        updateSaveBar();
    }
</script>

</body></html>
```
