let dongFeaturesCache = null

export async function loadDongFeatures() {
  if (dongFeaturesCache) return dongFeaturesCache
  const res = await fetch('/geo/seoul_dong.geojson')
  if (!res.ok) throw new Error('행정동 경계 데이터를 불러오지 못했습니다.')
  const data = await res.json()
  dongFeaturesCache = data.features
  return dongFeaturesCache
}
