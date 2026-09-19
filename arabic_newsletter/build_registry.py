"""Reproducible source inventory. Candidates are not labelled verified until probed."""
import json
from pathlib import Path

# name | region | country | language | website | feed (optional) | affiliation
DATA = '''
BBC World|global|GB|en|https://www.bbc.com/news|https://feeds.bbci.co.uk/news/world/rss.xml|public_broadcaster
BBC Middle East|global|GB|en|https://www.bbc.com/news|https://feeds.bbci.co.uk/news/world/middle_east/rss.xml|public_broadcaster
Al Jazeera|global|QA|ar|https://www.aljazeera.net|https://www.aljazeera.net/aljazeerarss/ar/all.xml|state_funded
France 24|global|FR|ar|https://www.france24.com/ar/|https://www.france24.com/ar/rss|public_broadcaster
DW World|global|DE|en|https://www.dw.com|https://rss.dw.com/rdf/rss-en-world|public_broadcaster
Guardian World|global|GB|en|https://www.theguardian.com/world|https://www.theguardian.com/world/rss|publisher
Middle East Eye|global|GB|en|https://www.middleeasteye.net|https://www.middleeasteye.net/rss|publisher
Defense News|global|US|en|https://www.defensenews.com|https://www.defensenews.com/arc/outboundfeeds/rss/category/global/|specialist
Breaking Defense|global|US|en|https://breakingdefense.com|https://breakingdefense.com/feed/|specialist
Bellingcat|global|NL|en|https://www.bellingcat.com|https://www.bellingcat.com/feed/|investigative
WAM|gcc|AE|ar|https://www.wam.ae/ar||official
SPA|gcc|SA|ar|https://www.spa.gov.sa||official
QNA|gcc|QA|ar|https://www.qna.org.qa/ar-QA||official
KUNA|gcc|KW|ar|https://www.kuna.net.kw||official
BNA|gcc|BH|ar|https://www.bna.bh||official
ONA|oman|OM|ar|https://omannews.gov.om||official
The National|gcc|AE|en|https://www.thenationalnews.com|https://www.thenationalnews.com/arc/outboundfeeds/rss/?outputType=xml|publisher
Al Arabiya|gcc|SA|ar|https://www.alarabiya.net|https://www.alarabiya.net/feed/rss2/ar.xml|broadcaster
IRNA|iran|IR|fa|https://www.irna.ir|https://www.irna.ir/rss|official
ISNA|iran|IR|fa|https://www.isna.ir|https://www.isna.ir/rss|affiliation_review
Mehr|iran|IR|fa|https://www.mehrnews.com|https://www.mehrnews.com/rss|affiliation_review
Iran International|iran|GB|fa|https://www.iranintl.com||diaspora
Anadolu|turkey|TR|tr|https://www.aa.com.tr/tr|https://www.aa.com.tr/tr/rss/default?cat=guncel|state_agency
TRT Haber|turkey|TR|tr|https://www.trthaber.com|https://www.trthaber.com/sondakika.rss|public_broadcaster
Bianet|turkey|TR|tr|https://bianet.org|https://bianet.org/feed|publisher
Shafaq|iraq|IQ|ar|https://shafaq.com/ar|https://shafaq.com/ar/rss|publisher
Iraqi News Agency|iraq|IQ|ar|https://ina.iq||official
Rudaw|iraq|IQ|en|https://www.rudaw.net/english|https://www.rudaw.net/english/rss.xml|broadcaster
Alsumaria|iraq|IQ|ar|https://www.alsumaria.tv||broadcaster
Al Masdar Online|yemen|YE|ar|https://almasdaronline.com||publisher
Belqees|yemen|YE|ar|https://belqees.net||broadcaster
Yemen Shabab|yemen|YE|ar|https://yemenshabab.net||broadcaster
Dabanga|sudan|SD|ar|https://www.dabangasudan.org/ar|https://www.dabangasudan.org/ar/feed|publisher
Sudan Tribune|sudan|SD|en|https://sudantribune.com|https://sudantribune.com/feed/|publisher
Sudan War Monitor|sudan|SD|en|https://sudanwarmonitor.com|https://sudanwarmonitor.com/feed|specialist
Studio Tamani|sahel|ML|fr|https://www.studiotamani.org|https://www.studiotamani.org/feed|local_radio
Sidwaya|sahel|BF|fr|https://www.sidwaya.info|https://www.sidwaya.info/feed/|state_publisher
Le Sahel|sahel|NE|fr|https://www.lesahel.org|https://www.lesahel.org/feed/|state_publisher
Alakhbar|sahel|MR|ar|https://alakhbar.info||publisher
Alwihda Info|sahel|TD|fr|https://www.alwihdainfo.com|https://www.alwihdainfo.com/xml/syndication.rss|publisher
APS Senegal|sahel|SN|fr|https://aps.sn|https://aps.sn/feed/|official
APS Algeria|north_africa|DZ|ar|https://www.aps.dz||official
TAP|north_africa|TN|ar|https://www.tap.info.tn/ar||official
MAP|north_africa|MA|ar|https://www.mapnews.ma/ar||official
Hespress|north_africa|MA|ar|https://www.hespress.com|https://www.hespress.com/feed|publisher
Mada Masr|egypt|EG|ar|https://www.madamasr.com/ar|https://www.madamasr.com/ar/feed/|publisher
Ahram Online|egypt|EG|en|https://english.ahram.org.eg||state_publisher
Libya Al Ahrar|north_africa|LY|ar|https://libyaalahrar.tv|https://libyaalahrar.tv/feed/|broadcaster
Al Wasat|north_africa|LY|ar|https://alwasat.ly||publisher
Dawn|pakistan|PK|en|https://www.dawn.com|https://www.dawn.com/feeds/home|publisher
Geo News|pakistan|PK|ur|https://urdu.geo.tv|https://urdu.geo.tv/rss/1|broadcaster
ISPR|pakistan|PK|en|https://ispr.gov.pk||official_military
TOLOnews|afghanistan|AF|fa|https://tolonews.com/fa|https://tolonews.com/feed|broadcaster
Pajhwok|afghanistan|AF|en|https://pajhwok.com|https://pajhwok.com/feed/|publisher
Amu TV|afghanistan|AF|fa|https://amu.tv/fa|https://amu.tv/fa/feed/|broadcaster
Radio Ergo|somalia|SO|so|https://radioergo.org|https://radioergo.org/feed/|local_radio
SONNA|somalia|SO|ar|https://sonna.so/ar|https://sonna.so/ar/feed/|official
Goobjoog|somalia|SO|so|https://goobjoog.com|https://goobjoog.com/feed/|broadcaster
Addis Standard|horn|ET|en|https://addisstandard.com|https://addisstandard.com/feed/|publisher
ENA|horn|ET|en|https://www.ena.et/web/eng||official
ADI|horn|DJ|fr|https://www.adi.dj||official
Shabait|horn|ER|en|https://shabait.com|https://shabait.com/feed/|official
WAFA|levant|PS|ar|https://www.wafa.ps||official
Maan|levant|PS|ar|https://www.maannews.net||publisher
Times of Israel|levant|IL|en|https://www.timesofisrael.com|https://www.timesofisrael.com/feed/|publisher
LOrient Today|levant|LB|en|https://today.lorientlejour.com|https://today.lorientlejour.com/rss|publisher
NNA|levant|LB|ar|https://www.nna-leb.gov.lb/ar||official
Enab Baladi|levant|SY|ar|https://www.enabbaladi.net|https://www.enabbaladi.net/feed/|publisher
SANA|levant|SY|ar|https://sana.sy||official
Petra|levant|JO|ar|https://petra.gov.jo||official
Al Mamlaka|levant|JO|ar|https://www.almamlakatv.com||broadcaster
'''

def main():
    sources=[]
    for i,line in enumerate(DATA.strip().splitlines(),1):
        name,region,country,language,website,feed,affiliation=line.split('|')
        sources.append(dict(id=f's{i:03}',name=name,region=region,country=country,language=language,
          website=website,feed=feed,affiliation=affiliation,enabled=True,verification_status='candidate',
          social_policy='discover_from_publisher_website'))
    path=Path(__file__).with_name('sources.json')
    path.write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{len(sources)} source candidates')
if __name__=='__main__': main()
