"""Canonical 121-area registry from Seoul's 실시간 도시데이터 관측지역 목록.

The service expanded from the original 82-area workbook to 121 areas (adding
a 공원 category and several additional 인구밀집지역/발달상권 entries), and
POI008-POI012 shifted/gained entries versus the old 82-area workbook:
POI008=경복궁, POI009=광화문·덕수궁, POI010=보신각, POI011=서울 암사동 유적
(new), POI012=창덕궁·종묘. Only the fields needed for matching and API
requests are kept here so runtime does not depend on a developer's Downloads
folder or an Excel parser.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SeoulHotspot:
    category: str
    number: int
    area_code: str
    area_name: str


SEOUL_HOTSPOTS: tuple[SeoulHotspot, ...] = (
    SeoulHotspot("관광특구", 1, "POI001", "강남 MICE 관광특구"),
    SeoulHotspot("관광특구", 2, "POI002", "동대문 관광특구"),
    SeoulHotspot("관광특구", 3, "POI003", "명동 관광특구"),
    SeoulHotspot("관광특구", 4, "POI004", "이태원 관광특구"),
    SeoulHotspot("관광특구", 5, "POI005", "잠실 관광특구"),
    SeoulHotspot("관광특구", 6, "POI006", "종로·청계 관광특구"),
    SeoulHotspot("관광특구", 7, "POI007", "홍대 관광특구"),
    SeoulHotspot("고궁·문화유산", 8, "POI008", "경복궁"),
    SeoulHotspot("고궁·문화유산", 9, "POI009", "광화문·덕수궁"),
    SeoulHotspot("고궁·문화유산", 10, "POI010", "보신각"),
    SeoulHotspot("고궁·문화유산", 11, "POI011", "서울 암사동 유적"),
    SeoulHotspot("고궁·문화유산", 12, "POI012", "창덕궁·종묘"),
    SeoulHotspot("인구밀집지역", 13, "POI013", "가산디지털단지역"),
    SeoulHotspot("인구밀집지역", 14, "POI014", "강남역"),
    SeoulHotspot("인구밀집지역", 15, "POI015", "건대입구역"),
    SeoulHotspot("인구밀집지역", 16, "POI016", "고덕역"),
    SeoulHotspot("인구밀집지역", 17, "POI017", "고속터미널역"),
    SeoulHotspot("인구밀집지역", 18, "POI018", "교대역"),
    SeoulHotspot("인구밀집지역", 19, "POI019", "구로디지털단지역"),
    SeoulHotspot("인구밀집지역", 20, "POI020", "구로역"),
    SeoulHotspot("인구밀집지역", 21, "POI021", "군자역"),
    SeoulHotspot("인구밀집지역", 22, "POI023", "대림역"),
    SeoulHotspot("인구밀집지역", 23, "POI024", "동대문역"),
    SeoulHotspot("인구밀집지역", 24, "POI025", "뚝섬역"),
    SeoulHotspot("인구밀집지역", 25, "POI026", "미아사거리역"),
    SeoulHotspot("인구밀집지역", 26, "POI027", "발산역"),
    SeoulHotspot("인구밀집지역", 27, "POI029", "사당역"),
    SeoulHotspot("인구밀집지역", 28, "POI030", "삼각지역"),
    SeoulHotspot("인구밀집지역", 29, "POI031", "서울대입구역"),
    SeoulHotspot("인구밀집지역", 30, "POI032", "서울식물원·마곡나루역"),
    SeoulHotspot("인구밀집지역", 31, "POI033", "서울역"),
    SeoulHotspot("인구밀집지역", 32, "POI034", "선릉역"),
    SeoulHotspot("인구밀집지역", 33, "POI035", "성신여대입구역"),
    SeoulHotspot("인구밀집지역", 34, "POI036", "수유역"),
    SeoulHotspot("인구밀집지역", 35, "POI037", "신논현역·논현역"),
    SeoulHotspot("인구밀집지역", 36, "POI038", "신도림역"),
    SeoulHotspot("인구밀집지역", 37, "POI039", "신림역"),
    SeoulHotspot("인구밀집지역", 38, "POI040", "신촌·이대역"),
    SeoulHotspot("인구밀집지역", 39, "POI041", "양재역"),
    SeoulHotspot("인구밀집지역", 40, "POI042", "역삼역"),
    SeoulHotspot("인구밀집지역", 41, "POI043", "연신내역"),
    SeoulHotspot("인구밀집지역", 42, "POI044", "오목교역·목동운동장"),
    SeoulHotspot("인구밀집지역", 43, "POI045", "왕십리역"),
    SeoulHotspot("인구밀집지역", 44, "POI046", "용산역"),
    SeoulHotspot("인구밀집지역", 45, "POI047", "이태원역"),
    SeoulHotspot("인구밀집지역", 46, "POI048", "장지역"),
    SeoulHotspot("인구밀집지역", 47, "POI049", "장한평역"),
    SeoulHotspot("인구밀집지역", 48, "POI050", "천호역"),
    SeoulHotspot("인구밀집지역", 49, "POI051", "총신대입구(이수)역"),
    SeoulHotspot("인구밀집지역", 50, "POI052", "충정로역"),
    SeoulHotspot("인구밀집지역", 51, "POI053", "합정역"),
    SeoulHotspot("인구밀집지역", 52, "POI054", "혜화역"),
    SeoulHotspot("인구밀집지역", 53, "POI055", "홍대입구역(2호선)"),
    SeoulHotspot("인구밀집지역", 54, "POI056", "회기역"),
    SeoulHotspot("발달상권", 55, "POI058", "가락시장"),
    SeoulHotspot("발달상권", 56, "POI059", "가로수길"),
    SeoulHotspot("발달상권", 57, "POI060", "광장(전통)시장"),
    SeoulHotspot("발달상권", 58, "POI061", "김포공항"),
    SeoulHotspot("발달상권", 59, "POI063", "노량진"),
    SeoulHotspot("발달상권", 60, "POI064", "덕수궁길·정동길"),
    SeoulHotspot("발달상권", 61, "POI066", "북촌한옥마을"),
    SeoulHotspot("발달상권", 62, "POI067", "서촌"),
    SeoulHotspot("발달상권", 63, "POI068", "성수카페거리"),
    SeoulHotspot("인구밀집지역", 64, "POI070", "쌍문역"),
    SeoulHotspot("발달상권", 65, "POI071", "압구정로데오거리"),
    SeoulHotspot("발달상권", 66, "POI072", "여의도"),
    SeoulHotspot("발달상권", 67, "POI073", "연남동"),
    SeoulHotspot("발달상권", 68, "POI074", "영등포 타임스퀘어"),
    SeoulHotspot("발달상권", 69, "POI076", "용리단길"),
    SeoulHotspot("발달상권", 70, "POI077", "이태원 앤틱가구거리"),
    SeoulHotspot("발달상권", 71, "POI078", "인사동"),
    SeoulHotspot("발달상권", 72, "POI079", "창동 신경제 중심지"),
    SeoulHotspot("발달상권", 73, "POI080", "청담동 명품거리"),
    SeoulHotspot("발달상권", 74, "POI081", "청량리 제기동 일대 전통시장"),
    SeoulHotspot("발달상권", 75, "POI082", "해방촌·경리단길"),
    SeoulHotspot("발달상권", 76, "POI083", "DDP(동대문디자인플라자)"),
    SeoulHotspot("발달상권", 77, "POI084", "DMC(디지털미디어시티)"),
    SeoulHotspot("공원", 78, "POI085", "강서한강공원"),
    SeoulHotspot("공원", 79, "POI086", "고척돔"),
    SeoulHotspot("공원", 80, "POI087", "광나루한강공원"),
    SeoulHotspot("공원", 81, "POI088", "광화문광장"),
    SeoulHotspot("공원", 82, "POI089", "국립중앙박물관·용산가족공원"),
    SeoulHotspot("공원", 83, "POI090", "난지한강공원"),
    SeoulHotspot("공원", 84, "POI091", "남산공원"),
    SeoulHotspot("공원", 85, "POI092", "노들섬"),
    SeoulHotspot("공원", 86, "POI093", "뚝섬한강공원"),
    SeoulHotspot("공원", 87, "POI094", "망원한강공원"),
    SeoulHotspot("공원", 88, "POI095", "반포한강공원"),
    SeoulHotspot("공원", 89, "POI096", "북서울꿈의숲"),
    SeoulHotspot("공원", 90, "POI098", "서리풀공원·몽마르뜨공원"),
    SeoulHotspot("공원", 91, "POI100", "서울대공원"),
    SeoulHotspot("공원", 92, "POI101", "서울숲공원"),
    SeoulHotspot("공원", 93, "POI102", "아차산"),
    SeoulHotspot("공원", 94, "POI103", "양화한강공원"),
    SeoulHotspot("공원", 95, "POI104", "어린이대공원"),
    SeoulHotspot("공원", 96, "POI105", "여의도한강공원"),
    SeoulHotspot("공원", 97, "POI106", "월드컵공원"),
    SeoulHotspot("공원", 98, "POI107", "응봉산"),
    SeoulHotspot("공원", 99, "POI108", "이촌한강공원"),
    SeoulHotspot("공원", 100, "POI109", "잠실종합운동장"),
    SeoulHotspot("공원", 101, "POI110", "잠실한강공원"),
    SeoulHotspot("공원", 102, "POI111", "잠원한강공원"),
    SeoulHotspot("공원", 103, "POI112", "청계산"),
    SeoulHotspot("발달상권", 104, "POI114", "북창동 먹자골목"),
    SeoulHotspot("발달상권", 105, "POI115", "남대문시장"),
    SeoulHotspot("발달상권", 106, "POI116", "익선동"),
    SeoulHotspot("인구밀집지역", 107, "POI117", "신정네거리역"),
    SeoulHotspot("인구밀집지역", 108, "POI118", "잠실새내역"),
    SeoulHotspot("인구밀집지역", 109, "POI119", "잠실역"),
    SeoulHotspot("발달상권", 110, "POI120", "잠실롯데타워·석촌호수"),
    SeoulHotspot("발달상권", 111, "POI121", "송리단길·호수단길"),
    SeoulHotspot("발달상권", 112, "POI122", "신촌 스타광장"),
    SeoulHotspot("공원", 113, "POI123", "보라매공원"),
    SeoulHotspot("공원", 114, "POI124", "서대문독립공원"),
    SeoulHotspot("공원", 115, "POI125", "안양천"),
    SeoulHotspot("공원", 116, "POI126", "여의서로"),
    SeoulHotspot("공원", 117, "POI127", "올림픽공원"),
    SeoulHotspot("공원", 118, "POI128", "홍제폭포"),
    SeoulHotspot("공원", 119, "POI129", "송현녹지광장"),
    SeoulHotspot("인구밀집지역", 120, "POI130", "시의회 앞"),
    SeoulHotspot("인구밀집지역", 121, "POI131", "숭례문"),
)


HOTSPOTS_BY_CODE = {area.area_code: area for area in SEOUL_HOTSPOTS}
HOTSPOTS_BY_NAME = {area.area_name: area for area in SEOUL_HOTSPOTS}

if len(SEOUL_HOTSPOTS) != 121 or len(HOTSPOTS_BY_CODE) != 121 or len(HOTSPOTS_BY_NAME) != 121:
    raise RuntimeError("서울시 121개 실시간 지역 목록에 중복 또는 누락이 있습니다.")


# Extra TourAPI title spellings. Canonical AREA_NM is always included by the
# matcher, and more specific aliases win over broad ones.
EXTRA_TITLE_ALIASES: dict[str, tuple[str, ...]] = {
    "POI001": ("코엑스", "COEX", "무역센터", "봉은사"),
    "POI002": ("동대문 패션타운", "두타몰"),
    "POI003": ("명동", "남산골한옥마을"),
    "POI004": ("이태원 관광",),
    "POI005": ("롯데월드 어드벤처", "롯데월드"),
    "POI006": ("청계천", "종로 관광", "종각역", "종각점"),
    "POI007": ("홍대거리", "홍대 걷고싶은거리"),
    "POI008": ("국립고궁박물관",),
    "POI009": ("덕수궁", "덕수궁돈덕전", "세종문화회관", "서울시청"),
    "POI011": ("암사동 유적", "선사유적"),
    "POI015": ("건대입구",),
    "POI017": ("서울고속버스터미널", "센트럴시티"),
    "POI032": ("서울식물원", "마곡나루역"),
    "POI037": ("신논현역", "논현역"),
    "POI040": ("신촌역", "이대역", "이화여대"),
    "POI044": ("오목교역", "목동운동장"),
    "POI051": ("총신대입구역", "이수역"),
    "POI055": ("홍대입구역",),
    "POI058": ("가락시장", "가락몰"),
    "POI060": ("광장시장",),
    "POI061": ("김포국제공항",),
    "POI063": ("노량진컵밥거리",),
    "POI064": ("덕수궁길", "정동길", "정동극장"),
    "POI066": ("북촌 8경", "북촌8경"),
    "POI067": ("통인시장",),
    "POI068": ("성수 카페거리",),
    "POI071": ("압구정로데오",),
    "POI072": ("더현대 서울", "여의도공원"),
    "POI073": ("경의선숲길",),
    "POI074": ("타임스퀘어",),
    "POI077": ("이태원 앤틱거리", "앤틱가구거리"),
    "POI078": ("쌈지길",),
    "POI081": ("청량리 전통시장", "제기동 전통시장"),
    "POI082": ("해방촌", "경리단길"),
    "POI083": ("동대문디자인플라자", "DDP"),
    "POI084": ("디지털미디어시티", "DMC"),
    "POI089": ("국립중앙박물관", "용산가족공원"),
    "POI091": ("N서울타워", "남산서울타워"),
    "POI098": ("서리풀공원", "몽마르뜨공원"),
    "POI100": ("서울랜드",),
    "POI101": ("서울숲",),
    "POI106": ("하늘공원", "노을공원"),
    "POI109": ("잠실야구장",),
    "POI114": ("북창동",),
    "POI115": ("남대문시장",),
    "POI116": ("익선동 한옥거리",),
    "POI120": ("롯데월드타워", "롯데타워", "석촌호수"),
    "POI121": ("송리단길", "호수단길"),
    "POI122": ("신촌 스타광장", "연세로"),
    "POI124": ("서대문형무소",),
    "POI129": ("열린송현",),
}


# Address matching is deliberately limited to explicit administrative
# neighbourhood tokens. Station-name substring matching in addresses causes
# false positives such as 신용산역 -> 용산역.
ADDRESS_ALIASES: dict[str, tuple[str, ...]] = {
    "POI003": ("명동1가", "명동2가"),
    "POI068": ("성수동1가", "성수동2가"),
    "POI072": ("여의도동",),
    "POI073": ("연남동",),
    "POI078": ("인사동",),
    "POI116": ("익선동",),
}
