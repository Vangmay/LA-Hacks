
export default function Home() {
  return (
    <div className="min-h-screen w-full bg-[#181c2f] flex flex-col items-center justify-center relative overflow-hidden font-sans">
      {/* Background vignette and overlays */}
      <div className="veridian-bg-overlay" />
      {/* Left particle field */}
      <svg className="particle-field left-0 top-0 h-full w-[30vw]" style={{position:'absolute',left:0,top:0}} width="400" height="800" viewBox="0 0 400 800">
        {Array.from({length: 180}).map((_,i) => {
          const y = i*4.2+Math.random()*8;
          const x = 60 + Math.pow(y/800,1.5)*180 + Math.random()*18;
          const r = Math.random()*2.5+0.7;
          const op = 0.3 + 0.7*(1-y/800);
          const fill = `url(#leftGrad)`;
          return <circle key={i} cx={x} cy={y} r={r} fill="#00eaff" opacity={op} style={{filter:'blur(0.5px)'}} />;
        })}
        <defs>
          <radialGradient id="leftGrad" cx="0.2" cy="0.5" r="1">
            <stop offset="0%" stopColor="#00eaff" stopOpacity="1" />
            <stop offset="100%" stopColor="#181c2f" stopOpacity="0" />
          </radialGradient>
        </defs>
      </svg>
      {/* Right particle field */}
      <svg className="particle-field right-0 top-0 h-full w-[30vw]" style={{position:'absolute',right:0,top:0}} width="400" height="800" viewBox="0 0 400 800">
        {Array.from({length: 180}).map((_,i) => {
          const y = i*4.2+Math.random()*8;
          const x = 340 - Math.pow(y/800,1.5)*180 - Math.random()*18;
          const r = Math.random()*2.5+0.7;
          const op = 0.3 + 0.7*(1-y/800);
          const fill = `url(#rightGrad)`;
          return <circle key={i} cx={x} cy={y} r={r} fill="#b388ff" opacity={op} style={{filter:'blur(0.5px)'}} />;
        })}
        <defs>
          <radialGradient id="rightGrad" cx="0.8" cy="0.5" r="1">
            <stop offset="0%" stopColor="#b388ff" stopOpacity="1" />
            <stop offset="100%" stopColor="#181c2f" stopOpacity="0" />
          </radialGradient>
        </defs>
      </svg>
      {/* Top bar */}
      <div className="absolute top-0 left-0 w-full flex items-center justify-between px-16 py-8 z-10">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full border-2 border-[#00eaff] flex items-center justify-center">
            <svg width="40" height="40" viewBox="0 0 40 40"><circle cx="20" cy="20" r="18" stroke="#00eaff" strokeWidth="2" fill="none" /></svg>
          </div>
          <span className="text-2xl tracking-widest font-semibold text-white" style={{fontFamily:'Fira Sans, sans-serif', letterSpacing:'0.22em'}}>
            VERIDI
            <span style={{color:'#b388ff', fontWeight:900, fontFamily:'Fira Sans, sans-serif', letterSpacing:'-0.1em'}}>A</span>N
          </span>
        </div>
        <div className="flex gap-8">
          <span className="text-white text-sm opacity-80 cursor-pointer">brightness</span>
          <span className="text-white text-sm opacity-80 cursor-pointer">person</span>
        </div>
      </div>

      {/* Centerpiece with concentric rings and connecting lines */}
      <div className="flex flex-col items-center justify-center w-full h-full z-10">
        <div className="relative flex flex-col items-center justify-center">
          {/* Central HUD: enhanced with layered, blurred, and animated rings */}
          <div className="central-hud absolute w-[700px] h-[700px] top-0 left-0 pointer-events-none">
            {/* Animated blurred rings */}
            <svg className="absolute animate-spin-slow" width="700" height="700" viewBox="0 0 700 700" style={{filter:'blur(8px)'}}>
              <circle cx="350" cy="350" r="320" stroke="#00eaff" strokeWidth="2.5" fill="none" opacity="0.18" />
            </svg>
            <svg className="absolute animate-spin-reverse-slower" width="700" height="700" viewBox="0 0 700 700" style={{filter:'blur(12px)'}}>
              <circle cx="350" cy="350" r="270" stroke="#b388ff" strokeWidth="3.5" fill="none" opacity="0.13" />
            </svg>
            <svg className="absolute animate-spin-slower" width="700" height="700" viewBox="0 0 700 700" style={{filter:'blur(18px)'}}>
              <circle cx="350" cy="350" r="200" stroke="#00eaff" strokeWidth="2.5" fill="none" opacity="0.10" />
            </svg>
            {/* Main HUD SVG with connecting lines, ticks, and gradients */}
            <svg className="absolute" width="700" height="700" viewBox="0 0 700 700" style={{filter:'drop-shadow(0 0 60px #00eaff66) drop-shadow(0 0 120px #b388ff44)'}}>
              <defs>
                <radialGradient id="hudGlow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#23243a" stopOpacity="0.7" />
                  <stop offset="80%" stopColor="#00eaff" stopOpacity="0.12" />
                  <stop offset="100%" stopColor="#b388ff" stopOpacity="0.08" />
                </radialGradient>
                <linearGradient id="hudRing" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stopColor="#00eaff" />
                  <stop offset="100%" stopColor="#b388ff" />
                </linearGradient>
              </defs>
              {/* Curved connecting lines to mode bubbles */}
              {/* Top (Review) */}
              <path d="M350 350 Q350 120 350 60" stroke="#00eaff" strokeWidth="3.5" fill="none" opacity="0.8" style={{filter:'blur(1.5px)'}} />
              <circle cx="350" cy="60" r="10" fill="#00eaff" opacity="0.8" style={{filter:'blur(2.5px)'}} />
              {/* Right (Execute) */}
              <path d="M350 350 Q600 350 640 350" stroke="#b388ff" strokeWidth="3.5" fill="none" opacity="0.8" style={{filter:'blur(1.5px)'}} />
              <circle cx="640" cy="350" r="10" fill="#b388ff" opacity="0.8" style={{filter:'blur(2.5px)'}} />
              {/* Left (Reader) */}
              <path d="M350 350 Q100 350 60 350" stroke="#00eaff" strokeWidth="3.5" fill="none" opacity="0.8" style={{filter:'blur(1.5px)'}} />
              <circle cx="60" cy="350" r="10" fill="#00eaff" opacity="0.8" style={{filter:'blur(2.5px)'}} />
              {/* Bottom (Research) */}
              <path d="M350 350 Q350 600 350 640" stroke="#b388ff" strokeWidth="3.5" fill="none" opacity="0.8" style={{filter:'blur(1.5px)'}} />
              <circle cx="350" cy="640" r="10" fill="#b388ff" opacity="0.8" style={{filter:'blur(2.5px)'}} />
              <circle cx="350" cy="350" r="300" stroke="url(#hudRing)" strokeWidth="3" fill="none" opacity="0.5" style={{filter:'blur(2.5px)'}} />
              {/* Main glowing ring */}
              <circle cx="350" cy="350" r="240" stroke="url(#hudRing)" strokeWidth="4" fill="none" opacity="0.8" style={{filter:'blur(1.5px)'}} />
              {/* Inner ring with ticks */}
              <circle cx="350" cy="350" r="180" stroke="#3a4a6b" strokeWidth="2" fill="none" opacity="0.7" />
              {/* Radial ticks */}
              {Array.from({length: 60}).map((_,i) => {
                const angle = (i/60)*2*Math.PI;
                const r1 = 180, r2 = i%5===0 ? 170 : 175;
                const x1 = 350 + r1*Math.cos(angle), y1 = 350 + r1*Math.sin(angle);
                const x2 = 350 + r2*Math.cos(angle), y2 = 350 + r2*Math.sin(angle);
                return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#00eaff" strokeWidth={i%5===0?2:1} opacity={i%5===0?0.5:0.2} />;
              })}
              {/* Glow overlay */}
              <circle cx="350" cy="350" r="220" fill="url(#hudGlow)" opacity="0.7" />
            </svg>
          </div>
          {/* Drop zone */}
          <div className="relative flex flex-col items-center justify-center w-[520px] h-[250px] rounded-2xl z-10 dropzone-glow"
            style={{
              background: 'rgba(24,28,47,0.85)',
              backdropFilter: 'blur(8px)',
              WebkitBackdropFilter: 'blur(8px)'
            }}>
            <div className="text-6xl mb-2 font-extrabold veridian-gradient-title" style={{fontFamily:'Fira Sans, sans-serif', letterSpacing:'0.08em', lineHeight:'1.05'}}>
              VERIDI
              <span className="veridian-gradient-a">A</span>N
            </div>
            <div className="mb-2 text-xl font-semibold veridian-gradient-sub" style={{letterSpacing:'0.04em',fontFamily:'Fira Sans, sans-serif'}}>
              INTERROGATE RESEARCH. <span className="veridian-gradient-reveal">REVEAL TRUTH.</span>
            </div>
            <div className="flex flex-col items-center mt-4">
              <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
                <g filter="url(#dropGlow)">
                  <path d="M28 10v22" stroke="#b388ff" strokeWidth="3.5" strokeLinecap="round"/>
                  <path d="M28 32l-8-8" stroke="#b388ff" strokeWidth="3.5" strokeLinecap="round"/>
                  <path d="M28 32l8-8" stroke="#b388ff" strokeWidth="3.5" strokeLinecap="round"/>
                  <rect x="12" y="40" width="32" height="6" rx="3" fill="#b388ff" opacity="0.18" />
                </g>
                <defs>
                  <filter id="dropGlow" x="0" y="0" width="56" height="56" filterUnits="userSpaceOnUse">
                    <feGaussianBlur stdDeviation="2.5" result="blur"/>
                    <feMerge>
                      <feMergeNode in="blur"/>
                      <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                  </filter>
                </defs>
              </svg>
              <div className="mt-2 text-white text-2xl font-bold dropzone-text-glow" style={{fontFamily:'Fira Sans, sans-serif', letterSpacing:'0.08em'}}>DROP A PAPER HERE</div>
              <div className="text-[#00eaff] text-sm mt-1">or paste <a href="#" className="underline">arXiv link</a></div>
            </div>
          </div>
        </div>
        {/* Mode bubbles */}
        <div className="absolute left-1/2 top-1/2 w-[700px] h-[700px] pointer-events-none" style={{transform: 'translate(-50%, -50%)'}}>
          {/* Mode bubbles aligned to the edges of the drop zone box */}
          {(() => {
            // Drop zone: 520x250, HUD: 700x700, center at (350,350)
            const boxW = 520, boxH = 250, hudC = 350;
            // Bubble diameter is 120px, so radius is 60px
            const bubbleR = 60;
            const positions = [
              { label: 'REVIEW', x: 0, y: -boxH/2 - bubbleR }, // top edge, move up
              { label: 'EXECUTE', x: boxW/2 + bubbleR, y: 0 }, // right edge, move right
              { label: 'READER', x: -boxW/2 - bubbleR, y: 0 }, // left edge, move left
              { label: 'RESEARCH', x: 0, y: boxH/2 + bubbleR }, // bottom edge, move down
            ];
            const nodes = [
              {
                label: 'REVIEW',
                desc: 'Verify claims',
                color: '#00eaff',
                icon: (
                  <svg width="120" height="120" viewBox="0 0 120 120">
                    <circle cx="60" cy="60" r="54" stroke="#00eaff" strokeWidth="3.5" fill="none" opacity="0.9" />
                    <circle cx="60" cy="60" r="12" fill="#fff" />
                    <circle cx="60" cy="24" r="8" fill="#fff" />
                    <circle cx="96" cy="60" r="8" fill="#fff" />
                    <circle cx="60" cy="96" r="8" fill="#fff" />
                    <circle cx="24" cy="60" r="8" fill="#fff" />
                    <line x1="60" y1="60" x2="60" y2="24" stroke="#fff" strokeWidth="3" />
                    <line x1="60" y1="60" x2="96" y2="60" stroke="#fff" strokeWidth="3" />
                    <line x1="60" y1="60" x2="60" y2="96" stroke="#fff" strokeWidth="3" />
                    <line x1="60" y1="60" x2="24" y2="60" stroke="#fff" strokeWidth="3" />
                    <line x1="60" y1="24" x2="96" y2="60" stroke="#fff" strokeWidth="1.8" opacity="0.5" />
                    <line x1="96" y1="60" x2="60" y2="96" stroke="#fff" strokeWidth="1.8" opacity="0.5" />
                    <line x1="60" y1="96" x2="24" y2="60" stroke="#fff" strokeWidth="1.8" opacity="0.5" />
                    <line x1="24" y1="60" x2="60" y2="24" stroke="#fff" strokeWidth="1.8" opacity="0.5" />
                  </svg>
                ),
                glow: '0 0 48px 16px #00eaff, 0 0 96px 32px #00eaff55',
              },
              {
                label: 'EXECUTE',
                desc: 'Test empirically',
                color: '#b388ff',
                icon: (
                  <svg width="120" height="120" viewBox="0 0 120 120">
                    <circle cx="60" cy="60" r="54" stroke="#b388ff" strokeWidth="3.5" fill="none" opacity="0.9" />
                    <rect x="32" y="54" width="16" height="12" rx="3" fill="#fff" />
                    <rect x="54" y="54" width="16" height="12" rx="3" fill="#fff" />
                    <rect x="76" y="54" width="16" height="12" rx="3" fill="#fff" />
                    <path d="M92 60h12" stroke="#fff" strokeWidth="3.5" />
                    <circle cx="108" cy="60" r="4.5" fill="#fff" />
                    <path d="M48 60h6" stroke="#fff" strokeWidth="3.5" />
                    <path d="M70 60h6" stroke="#fff" strokeWidth="3.5" />
                    <circle cx="32" cy="60" r="4.5" fill="#fff" />
                  </svg>
                ),
                glow: '0 0 48px 16px #b388ff, 0 0 96px 32px #b388ff55',
              },
              {
                label: 'READER',
                desc: 'Understand deeply',
                color: '#00eaff',
                icon: (
                  <svg width="120" height="120" viewBox="0 0 120 120">
                    <circle cx="60" cy="60" r="54" stroke="#00eaff" strokeWidth="3.5" fill="none" opacity="0.9" />
                    <polygon points="60,38 100,60 60,82 20,60" fill="#fff" opacity="0.2" />
                    <polygon points="60,50 90,66 60,82 30,66" fill="#fff" opacity="0.4" />
                    <polygon points="60,62 80,72 60,82 40,72" fill="#fff" opacity="0.7" />
                    <polygon points="60,72 72,80 60,88 48,80" fill="#fff" />
                  </svg>
                ),
                glow: '0 0 48px 16px #00eaff, 0 0 96px 32px #00eaff55',
              },
              {
                label: 'RESEARCH',
                desc: 'Expand ideas',
                color: '#b388ff',
                icon: (
                  <svg width="120" height="120" viewBox="0 0 120 120">
                    <circle cx="60" cy="60" r="54" stroke="#b388ff" strokeWidth="3.5" fill="none" opacity="0.9" />
                    <circle cx="60" cy="60" r="12" fill="#fff" />
                    <circle cx="60" cy="24" r="8" fill="#fff" />
                    <circle cx="96" cy="60" r="8" fill="#fff" />
                    <circle cx="60" cy="96" r="8" fill="#fff" />
                    <circle cx="24" cy="60" r="8" fill="#fff" />
                    <line x1="60" y1="60" x2="60" y2="24" stroke="#fff" strokeWidth="3" />
                    <line x1="60" y1="60" x2="96" y2="60" stroke="#fff" strokeWidth="3" />
                    <line x1="60" y1="60" x2="60" y2="96" stroke="#fff" strokeWidth="3" />
                    <line x1="60" y1="60" x2="24" y2="60" stroke="#fff" strokeWidth="3" />
                    <line x1="60" y1="24" x2="96" y2="60" stroke="#fff" strokeWidth="1.8" opacity="0.5" />
                    <line x1="96" y1="60" x2="60" y2="96" stroke="#fff" strokeWidth="1.8" opacity="0.5" />
                    <line x1="60" y1="96" x2="24" y2="60" stroke="#fff" strokeWidth="1.8" opacity="0.5" />
                    <line x1="24" y1="60" x2="60" y2="24" stroke="#fff" strokeWidth="1.8" opacity="0.5" />
                  </svg>
                ),
                glow: '0 0 48px 16px #b388ff, 0 0 96px 32px #b388ff55',
              },
            ];
            return positions.map((pos, i) => (
              <div
                key={nodes[i].label}
                className="absolute"
                style={{
                  left: '50%',
                  top: '50%',
                  transform: `translate(-50%, -50%) translate(${pos.x}px, ${pos.y}px)`
                }}
              >
                <div className="flex flex-col items-center" style={{maxWidth: '120px'}}>
                  <div style={{ boxShadow: nodes[i].glow, borderRadius: '50%' }}>{nodes[i].icon}</div>
                  <div className="font-bold mt-2 text-xl tracking-wide text-center" style={{ color: nodes[i].color, maxWidth: '110px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{nodes[i].label}</div>
                  <div className="text-white text-xs opacity-80 text-center" style={{maxWidth: '110px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>{nodes[i].desc}</div>
                </div>
              </div>
            ));
          })()}
        </div>
      </div>
      {/* Upload instructions */}
      <div className="absolute left-1/2" style={{bottom: '1.2rem', transform: 'translateX(-50%)', color: '#b388ff', letterSpacing: '0.12em', fontFamily: 'Fira Sans, sans-serif', fontSize: '1.15rem', opacity: 0.8, zIndex: 20}}>UPLOAD A PAPER TO ACTIVATE MODES</div>
    </div>
  );
}
