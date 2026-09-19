"""Synthetic Arabic fixture. Never used as a live fallback."""
from datetime import datetime, timezone
from .core import REGIONS, edition_window

BASE={
 'gcc':'الإمارات تراجع إجراءات الجاهزية في الموانئ والمطارات بالتوازي مع اتصالات إقليمية',
 'iran':'طهران تعلن تحديثاً بشأن الانتشار العسكري والاتصالات الدبلوماسية الإقليمية',
 'turkey':'أنقرة تكثف المشاورات الأمنية والدبلوماسية بشأن تطورات الإقليم',
 'iraq':'بغداد تتابع أمن الحدود وتحركات الفصائل والاتصالات مع دول الجوار',
 'yemen':'تقارير عن تحركات عسكرية ومفاوضات مرتبطة بأمن البحر الأحمر',
 'sudan':'تطورات ميدانية واتصالات سياسية بشأن مسار القتال وحماية المدنيين',
 'sahel':'متابعة الانتشار الأمني والتحولات السياسية وتهديد الجماعات المسلحة في الساحل',
 'north_africa':'تحركات أمنية ودبلوماسية في شمال أفريقيا مع تركيز على الحدود والممرات البحرية',
 'pakistan':'إسلام آباد تراجع إجراءات الأمن الداخلي والحدودي والتنسيق العسكري',
 'afghanistan':'كابل تبحث ملفات الأمن الحدودي والعلاقات الإقليمية مع دول الجوار',
 'horn':'تطورات أمنية وسياسية في إثيوبيا وجيبوتي وإريتريا ومتابعة الملاحة في البحر الأحمر',
 'somalia':'الصومال: تطورات أمنية وسياسية ومتابعة الأوضاع في مقديشو والأقاليم',
 'levant':'لبنان وسوريا: متابعة أمن الحدود والانتشار العسكري والاتصالات السياسية',
 'palestine_israel':'فلسطين / إسرائيل: تطورات ميدانية واتصالات بشأن غزة والضفة والقدس',
 'jordan':'الأردن يرفع مستوى المتابعة الأمنية والدبلوماسية لتطورات الإقليم',
}

EXTRA=[
 ('gcc','الإمارات تصدر تحديثاً حكومياً يتعلق بالسلامة العامة واستمرارية الخدمات الحيوية','low','AE'),
 ('gcc','الإمارات تتابع حركة الطيران والمجال الجوي وتصدر إرشادات تشغيلية محدثة','low','AE'),
 ('palestine_israel','تحديث إضافي حول المفاوضات والوضع الإنساني والتحركات الميدانية في غزة','high','PS'),
 ('jordan','عمّان تكثف التنسيق مع الشركاء الإقليميين بشأن الحدود والمساعدات','medium','JO'),
]

def event(region,title,severity,country,index,long=False):
    summary='هذا نص اصطناعي لاختبار تصميم موجز قيادي كثيف البيانات وليس خبراً حقيقياً. يلخص التطور في صياغة منسوبة ويحافظ على حدود المعلومات المتاحة، مع فصل الوقائع عن التقدير التحليلي.'
    assessment='قد يؤثر التطور في مستوى الجاهزية أو مسار التنسيق الإقليمي؛ ولا تكفي البيانات المتاحة لاستنتاج تغير ميداني نهائي.'
    watch='متابعة البيانات الرسمية اللاحقة، مؤشرات الحركة الميدانية، وأي تغير موثق في الإجراءات أو المواقف.'
    if long:
        title+=' مع استمرار الاتصالات وتباين المواقف الرسمية وارتفاع الحاجة إلى متابعة المؤشرات الميدانية خلال الساعات المقبلة'
        summary+=' ويضيف المثال الطويل سطراً إضافياً لاختبار التفاف النص العربي، كثافة المعلومات، تباعد الفقرات، ووضوح المراجع من دون تداخل مع الحدود.'
    return dict(region=region,topic='security',title_ar=title,summary_ar=summary,assessment_ar=assessment,
      watch_ar=watch,severity=severity,status_ar='تقرير منسوب',fingerprint='sample-'+str(index),
      source_ids=['sample-'+str(index)],sources=[dict(id='sample-'+str(index),source='مصدر تجريبي — ليس مصدراً إخبارياً',
      url='https://example.com/synthetic/'+str(index),published=0,affiliation='synthetic',kind='news',country=country)])

def fixture(long=False):
    start,end=edition_window(datetime.now(timezone.utc)); events=[]
    countries={'gcc':'AE','iran':'IR','turkey':'TR','iraq':'IQ','yemen':'YE','sudan':'SD','sahel':'ML',
      'north_africa':'EG','pakistan':'PK','afghanistan':'AF','horn':'ET','somalia':'SO','levant':'LB','palestine_israel':'PS','jordan':'JO'}
    for i,region in enumerate(REGIONS):
        sev='high' if region in ('palestine_israel','iran','yemen','sudan') else 'medium'
        e=event(region,BASE[region],sev,countries[region],i,long); e['sources'][0]['published']=end.timestamp()-600; events.append(e)
    for j,(region,title,sev,country) in enumerate(EXTRA,len(events)):
        e=event(region,title,sev,country,j,long); e['sources'][0]['published']=end.timestamp()-900; events.append(e)
    return dict(sample=True,window_start=start.isoformat(),window_end=end.isoformat(),events=events,input_count=84,
      health=[dict(id='sample-'+r,name='مصدر تجريبي',region=r,country='SAMPLE',status='active') for r in REGIONS])
