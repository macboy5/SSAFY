export function loadKakaoSdk(apiKey) {
  if (window.kakao?.maps) return new Promise((resolve) => window.kakao.maps.load(resolve))
  if (window.__seoulMateKakaoMapPromise) return window.__seoulMateKakaoMapPromise

  window.__seoulMateKakaoMapPromise = new Promise((resolve, reject) => {
    document.querySelector('script[data-kakao-map]')?.remove()
    const script = document.createElement('script')
    script.dataset.kakaoMap = 'true'
    script.async = true
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${encodeURIComponent(apiKey)}&autoload=false&libraries=clusterer`
    script.onload = () => {
      if (!window.kakao?.maps?.load) {
        reject(new Error('SDK 객체를 초기화하지 못했습니다.'))
        return
      }
      window.kakao.maps.load(resolve)
    }
    script.onerror = () => reject(new Error('카카오 서버가 지도 SDK 요청을 거부했습니다.'))
    document.head.appendChild(script)
  })
  return window.__seoulMateKakaoMapPromise
}

export function resetKakaoSdk() {
  delete window.__seoulMateKakaoMapPromise
}
