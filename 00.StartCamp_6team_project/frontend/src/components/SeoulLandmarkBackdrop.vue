<template>
  <div class="landmark-backdrop" aria-hidden="true">
    <span class="landmark palace">
      <svg viewBox="0 0 120 92" role="presentation">
        <path d="M15 43 31 32h58l16 11M24 43h72M31 32l8-10h42l8 10M35 22h50" />
        <path d="M28 48h64v31H28zM39 49v30M52 49v30M68 49v30M81 49v30M22 79h76" />
        <path d="M52 58h16v21H52zM18 43h84" />
      </svg>
    </span>

    <span class="landmark namsan">
      <svg viewBox="0 0 84 126" role="presentation">
        <path d="M42 5v24M37 14h10M35 29h14l3 14H32zM26 43h32l5 11H21z" />
        <path d="M31 54h22l4 14H27zM35 68h14l5 43H30zM24 111h36M17 120h50" />
        <path d="M39 78h6M37 91h10M34 104h16" />
      </svg>
    </span>

    <span class="landmark lotte">
      <svg viewBox="0 0 76 132" role="presentation">
        <path d="M38 5c-1 20-7 31-15 43-6 9-9 25-8 46h46c1-21-2-37-8-46C45 36 39 25 38 5Z" />
        <path d="M30 45h16M23 63h30M18 82h40M16 98h44M12 110h52v14H12z" />
        <path d="M30 110v14M46 110v14" />
      </svg>
    </span>

    <span class="landmark bridge">
      <svg viewBox="0 0 150 82" role="presentation">
        <path d="M8 31h134M17 31v21M40 31v21M63 31v21M87 31v21M110 31v21M133 31v21" />
        <path d="M17 52c7-15 16-15 23 0 7-15 16-15 23 0 7-15 17-15 24 0 7-15 16-15 23 0 7-15 16-15 23 0" />
        <path d="M5 63c17-7 31 7 48 0s31 7 48 0 28 4 44 0M14 74c15-5 27 5 42 0s27 5 42 0 25 4 39 0" />
      </svg>
    </span>

    <span class="landmark gate">
      <svg viewBox="0 0 118 92" role="presentation">
        <path d="M13 35 29 25h60l16 10M20 36h78M31 25l8-10h40l8 10M35 15h48" />
        <path d="M26 42h66v16H26zM32 58h54v24H32zM23 82h72" />
        <path d="M50 82V68c0-6 4-10 9-10s9 4 9 10v14M40 43v15M59 43v15M78 43v15" />
      </svg>
    </span>
  </div>
</template>

<style scoped>
.landmark-backdrop{position:fixed;inset:78px 0 0;z-index:0;overflow:hidden;pointer-events:none}
.landmark{--x1:32px;--y1:-30px;--x2:-22px;--y2:-54px;--x3:26px;--y3:16px;--tilt:0deg;position:absolute;display:block;color:var(--accent);opacity:.19;filter:drop-shadow(0 14px 24px color-mix(in srgb,var(--ink) 12%,transparent));transform-origin:50% 55%;animation:landmark-float 9.4s cubic-bezier(.45,.05,.55,.95) infinite;will-change:transform}
.landmark svg{display:block;width:100%;height:auto;overflow:visible;fill:none;stroke:currentColor;stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}
.palace{left:2.2%;top:12%;width:112px;--tilt:-2deg;animation-duration:8.8s}
.namsan{right:4.2%;top:10%;width:70px;--x1:-31px;--y1:-48px;--x2:20px;--y2:-25px;--x3:-15px;--y3:19px;--tilt:1deg;animation-delay:-6s;animation-duration:10.4s}
.lotte{left:4.8%;top:57%;width:62px;--x1:42px;--y1:-38px;--x2:18px;--y2:-62px;--x3:-26px;--y3:-18px;--tilt:-1deg;animation-delay:-9s;animation-duration:11.2s;color:var(--ink);opacity:.145}
.bridge{right:2.4%;top:67%;width:138px;--x1:-46px;--y1:-26px;--x2:-20px;--y2:-50px;--x3:29px;--y3:-14px;--tilt:1deg;animation-delay:-3s;animation-duration:9.6s}
.gate{right:15%;top:39%;width:94px;--x1:31px;--y1:-44px;--x2:-23px;--y2:-26px;--x3:18px;--y3:19px;--tilt:-1deg;animation-delay:-8s;animation-duration:10.8s;color:var(--ink);opacity:.14}
@keyframes landmark-float{
  0%,100%{transform:translate3d(0,0,0) rotate(var(--tilt)) scale(1)}
  28%{transform:translate3d(var(--x1),var(--y1),0) rotate(calc(var(--tilt) + 2deg)) scale(1.025)}
  55%{transform:translate3d(var(--x2),var(--y2),0) rotate(calc(var(--tilt) - 1.5deg)) scale(.99)}
  78%{transform:translate3d(var(--x3),var(--y3),0) rotate(calc(var(--tilt) + 1deg)) scale(1.015)}
}
@media(max-width:900px){.palace{left:-2%;width:96px}.namsan{right:2%;width:62px}.lotte{left:1%;width:54px}.bridge{right:-4%;width:118px}.gate{right:9%;width:82px}}
@media(max-width:640px){.landmark-backdrop{inset:70px 0 0}.landmark{--x1:22px;--y1:-28px;--x2:-15px;--y2:-39px;--x3:17px;--y3:12px}.palace{left:-7%;top:18%;width:88px;opacity:.16}.namsan{right:-1%;top:8%;width:58px;opacity:.17;--x1:-22px;--y1:-36px;--x2:14px;--y2:-20px;--x3:-11px;--y3:14px}.gate{right:-5%;top:65%;width:76px;opacity:.13}.lotte,.bridge{display:none}}
@media(max-width:400px){.gate{display:none}}
@media(prefers-reduced-motion:reduce){.landmark{animation:none;will-change:auto}}
</style>
