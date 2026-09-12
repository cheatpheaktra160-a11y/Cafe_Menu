"use client";

import { useEffect, useRef, useState } from 'react';
import { ArrowRight, Github, Google, Apple } from 'lucide-react';

export default function ModernLoginSignup() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isLogin, setIsLogin] = useState(true);

  useEffect(() => {
    let active = true;
    let renderer: any;
    let geometry: any;
    let material: any;
    let scene: any;
    let camera: any;
    let animationId: number;

    const initThree = (THREE: any) => {
      if (!canvasRef.current || !active) return;
      const canvas = canvasRef.current;
      renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: false });
      renderer.setPixelRatio(window.devicePixelRatio);
      renderer.setSize(window.innerWidth, window.innerHeight);

      scene = new THREE.Scene();
      camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

      const uniforms = {
        u_time: { value: 0 },
        u_resolution: { value: new THREE.Vector2(window.innerWidth * 2, window.innerHeight * 2) },
        u_opacities: { value: [0.3, 0.3, 0.3, 0.5, 0.5, 0.5, 0.8, 0.8, 0.8, 1.0] },
        u_colors: {
          value: [
            new THREE.Vector3(1, 1, 1),
            new THREE.Vector3(1, 1, 1),
            new THREE.Vector3(1, 1, 1),
            new THREE.Vector3(1, 1, 1),
            new THREE.Vector3(1, 1, 1),
            new THREE.Vector3(1, 1, 1),
          ],
        },
        u_total_size: { value: 20.0 },
        u_dot_size: { value: 6.0 },
        u_reverse: { value: 0 },
      };

      material = new THREE.ShaderMaterial({
        vertexShader: `
          precision mediump float;
          uniform vec2 u_resolution;
          out vec2 fragCoord;
          void main() {
            gl_Position = vec4(position, 1.0);
            fragCoord = (position.xy + 1.0) * 0.5 * u_resolution;
            fragCoord.y = u_resolution.y - fragCoord.y;
          }
        `,
        fragmentShader: `
          precision mediump float;
          in vec2 fragCoord;

          uniform float u_time;
          uniform float u_opacities[10];
          uniform vec3 u_colors[6];
          uniform float u_total_size;
          uniform float u_dot_size;
          uniform vec2 u_resolution;
          uniform int u_reverse;

          out vec4 fragColor;

          float PHI = 1.61803398874989484820459;
          float random(vec2 xy) {
              return fract(tan(distance(xy * PHI, xy) * 0.5) * xy.x);
          }

          void main() {
              vec2 st = fragCoord.xy;
              st.x -= abs(floor((mod(u_resolution.x, u_total_size) - u_dot_size) * 0.5));
              st.y -= abs(floor((mod(u_resolution.y, u_total_size) - u_dot_size) * 0.5));

              float opacity = step(0.0, st.x) * step(0.0, st.y);

              vec2 st2 = vec2(int(st.x / u_total_size), int(st.y / u_total_size));

              float frequency = 5.0;
              float show_offset = random(st2);
              float rand = random(st2 * floor((u_time / frequency) + show_offset + frequency));
              opacity *= u_opacities[int(rand * 10.0)];
              opacity *= 1.0 - step(u_dot_size / u_total_size, fract(st.x / u_total_size));
              opacity *= 1.0 - step(u_dot_size / u_total_size, fract(st.y / u_total_size));

              vec3 color = u_colors[int(show_offset * 6.0)];

              float animation_speed_factor = 3.0;
              vec2 center_grid = u_resolution / 2.0 / u_total_size;
              float dist_from_center = distance(center_grid, st2);

              float timing_offset_intro = dist_from_center * 0.01 + (random(st2) * 0.15);

              float current_timing_offset = timing_offset_intro;
              opacity *= step(current_timing_offset, u_time * animation_speed_factor);
              opacity *= clamp((1.0 - step(current_timing_offset + 0.1, u_time * animation_speed_factor)) * 1.25, 1.0, 1.25);

              fragColor = vec4(color, opacity);
              fragColor.rgb *= fragColor.a;
          }
        `,
        uniforms,
        glslVersion: THREE.GLSL3,
        blending: THREE.CustomBlending,
        blendSrc: THREE.SrcAlphaFactor,
        blendDst: THREE.OneFactor,
        transparent: true,
      });

      geometry = new THREE.PlaneGeometry(2, 2);
      const mesh = new THREE.Mesh(geometry, material);
      scene.add(mesh);

      const startTime = performance.now();
      const animate = () => {
        if (!active) return;
        animationId = requestAnimationFrame(animate);
        uniforms.u_time.value = (performance.now() - startTime) / 1000.0;
        renderer.render(scene, camera);
      };
      animate();

      const handleResize = () => {
        renderer.setSize(window.innerWidth, window.innerHeight);
        uniforms.u_resolution.value.set(window.innerWidth * 2, window.innerHeight * 2);
      };
      window.addEventListener('resize', handleResize);

      return () => {
        window.removeEventListener('resize', handleResize);
      };
    };

    if ((window as any).THREE) {
      const cleanUp = initThree((window as any).THREE);
      return () => {
        active = false;
        if (cleanUp) cleanUp();
        if (animationId) cancelAnimationFrame(animationId);
        if (renderer) renderer.dispose();
        if (geometry) geometry.dispose();
        if (material) material.dispose();
      };
    } else {
      const script = document.createElement('script');
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
      script.async = true;
      script.onload = () => {
        if ((window as any).THREE) {
          const cleanUp = initThree((window as any).THREE);
        }
      };
      document.head.appendChild(script);
    }

    return () => {
      active = false;
      if (animationId) cancelAnimationFrame(animationId);
      if (renderer) renderer.dispose();
      if (geometry) geometry.dispose();
      if (material) material.dispose();
    };
  }, []);

  const socialBtn: React.CSSProperties = {
    width: '100%',
    padding: '0.65rem',
    borderRadius: 6,
    border: '1px solid #333',
    background: 'transparent',
    color: '#fff',
    fontWeight: 500,
    fontSize: '0.875rem',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem',
    marginBottom: '0.4rem',
  };
  const input: React.CSSProperties = {
    width: '100%',
    padding: '0.65rem 0.85rem',
    borderRadius: 6,
    border: '1px solid #333',
    background: '#000',
    color: '#fff',
    fontSize: '0.875rem',
    outline: 'none',
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#070707] text-white font-sans">
      <canvas ref={canvasRef} className="absolute inset-0 z-0" />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,0,0,0.75)_0%,rgba(0,0,0,0)_100%)]" />
      <div className="relative z-10 mx-4 w-full max-w-md rounded-[1.25rem] border border-white/10 bg-[#121212]/95 p-8 shadow-[0_24px_80px_rgba(0,0,0,0.85)] backdrop-blur-xl sm:p-10">
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-full border border-white/10 bg-white/10 text-lg font-semibold text-white shadow-inner shadow-black/20">
            JS
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">
            {isLogin ? 'Sign in to Account' : 'Sign up for Account'}
          </h1>
          <p className="mt-3 max-w-xs text-sm text-slate-300">
            {isLogin
              ? 'Sign in to your Account.'
              : 'Create a new account to get started.'}
          </p>
        </div>

        <form className="mb-6 flex flex-col gap-4" onSubmit={(e) => e.preventDefault()}>
          <div className="grid gap-4">
            {!isLogin && (
              <input className="rounded-xl border border-white/10 bg-[#111111]/80 px-4 py-3 text-sm text-white outline-none transition focus:border-coffee-400" placeholder="Full Name" type="text" required />
            )}
            <input className="rounded-xl border border-white/10 bg-[#111111]/80 px-4 py-3 text-sm text-white outline-none transition focus:border-coffee-400" placeholder="name@work-email.com" type="email" required />
            <button className="rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-100" type="submit">
              {isLogin ? 'Continue with Email' : 'Sign Up with Email'}
            </button>
          </div>
        </form>

        <div className="relative py-4 text-center">
          <div className="absolute left-1/2 top-1/2 h-px w-full -translate-x-1/2 bg-white/10" />
          <span className="relative z-10 bg-[#121212] px-3 text-xs uppercase tracking-[0.2em] text-slate-400">
            Or continue with
          </span>
        </div>

        <div className="grid gap-3">
          <button className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white transition hover:border-coffee-200 hover:bg-white/10" style={socialBtn}>
            <Google size={16} /> Continue with Google
          </button>
          <button className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white transition hover:border-coffee-200 hover:bg-white/10" style={socialBtn}>
            <Github size={16} /> Continue with GitHub
          </button>
          <button className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white transition hover:border-coffee-200 hover:bg-white/10" style={socialBtn}>
            <Apple size={16} /> Continue with Apple
          </button>
        </div>

        <div className="mt-7 text-center text-sm text-slate-400">
          {isLogin ? (
            <>Don't have an account?{' '}
              <button onClick={() => setIsLogin(false)} className="font-semibold text-white hover:text-coffee-200">
                Sign Up
              </button>
            </>
          ) : (
            <>Already have an account?{' '}
              <button onClick={() => setIsLogin(true)} className="font-semibold text-white hover:text-coffee-200">
                Sign In
              </button>
            </>
          )}
        </div>

        <div className="mt-8 rounded-3xl border border-white/5 bg-white/5 p-4 text-center text-[0.78rem] leading-6 text-slate-400">
          By proceeding, you agree to creating a Vercel account subject to our{' '}
          <a className="text-white underline" href="#">
            Terms of Service
          </a>{' '}
          and{' '}
          <a className="text-white underline" href="#">
            Privacy Policy
          </a>.
        </div>
      </div>
    </div>
  );
}
