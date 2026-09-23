"""Synthetic Arabic fixture. Never used as a live fallback."""
from datetime import datetime, timezone
from .core import REGIONS, edition_window

BASE={
 'gcc':'الإمارات والخليج: تحديثات في الجاهزية والاتصالات الإقليمية',
 'oman':'عُمان: متابعة أمن الملاحة والاتصالات الإقليمية',
 'iran':'إيران: اتصالات دبلوماسية ومؤشرات أمنية قيد المتابعة',
 'turkey':'تركيا: مشاورات أمنية ودبلوماسية بشأن الإقليم',
 'iraq':'العراق: متابعة الحدود وتحركات الفصائل والاتصالات',
 'yemen':'اليمن: تطورات مرتبطة بأمن البحر الأحمر ومسار التهدئة',
 'egypt':'مصر: متابعة قناة السويس وسيناء والتحركات الدبلوماسية',
 'sudan':'السودان: تطورات ميدانية واتصالات لحماية المدنيين',
 'sahel':'الساحل الأفريقي: تحولات أمنية وتهديدات مسلحة',
 'north_africa':'شمال أفريقيا: تحركات أمنية ودبلوماسية متباينة',
 'pakistan':'باكستان: مراجعة الأمن الداخلي والحدودي',
 'afghanistan':'أفغانستان: ملفات الحدود والأمن والعلاقات الإقليمية',
 'horn':'القرن الأفريقي: تطورات أمنية وتأثيرات على الملاحة',
 'somalia':'الصومال: متابعة أمنية وسياسية في مقديشو والأقاليم',
 'levant':'لبنان وسوريا: متابعة الحدود والاتصالات السياسية',
 'palestine_israel':'فلسطين وإسرائيل: تطورات ميدانية واتصالات بشأن غزة',
 'jordan':'الأردن: رفع مستوى المتابعة الأمنية والدبلوماسية',
}

SUMMARY={
 'gcc':'تحديثات في الجاهزية بالموانئ والمطارات بالتوازي مع اتصالات دبلوماسية إقليمية.',
 'oman':'متابعة أمن الموانئ والممرات البحرية مع استمرار قنوات الوساطة والتنسيق.',
 'iran':'اتصالات دبلوماسية متواصلة بالتوازي مع مؤشرات أمنية تتطلب مراقبة دقيقة.',
 'turkey':'مشاورات إقليمية مكثفة حول الأمن والتهدئة ومسارات التعاون الدبلوماسي.',
 'iraq':'متابعة لأمن الحدود وتحركات الفصائل مع اتصالات مستمرة مع دول الجوار.',
 'yemen':'تطورات ميدانية مرتبطة بالبحر الأحمر مع استمرار مسارات التفاوض والتهدئة.',
 'egypt':'تركيز على أمن قناة السويس وسيناء مع نشاط دبلوماسي إقليمي متزايد.',
 'sudan':'تطورات ميدانية مستمرة بالتوازي مع اتصالات سياسية لحماية المدنيين.',
 'sahel':'نشاط أمني متزايد وتحولات سياسية مع استمرار تهديد الجماعات المسلحة.',
 'north_africa':'صورة أمنية وسياسية متباينة مع متابعة الحدود والممرات البحرية.',
 'pakistan':'إجراءات أمنية داخلية وحدودية مع استمرار التنسيق الإقليمي والعسكري.',
 'afghanistan':'متابعة لملفات الحدود والأمن والعلاقات مع دول الجوار.',
 'horn':'تطورات إقليمية تؤثر في أمن البحر الأحمر وخليج عدن وحركة الملاحة.',
 'somalia':'متابعة أمنية وسياسية مع تركيز على مقديشو والأقاليم وحماية المؤسسات.',
 'levant':'متابعة أمن الحدود والانتشار والاتصالات السياسية في لبنان وسوريا.',
 'palestine_israel':'تطورات ميدانية واتصالات دبلوماسية بشأن غزة والضفة والقدس.',
 'jordan':'متابعة أمنية ودبلوماسية مكثفة لتداعيات التطورات الإقليمية.',
}

EXTRA=[
 ('gcc','الإمارات تصدر تحديثاً حكومياً يتعلق بالسلامة العامة واستمرارية الخدمات الحيوية','low','AE'),
 ('gcc','الإمارات تتابع حركة الطيران والمجال الجوي وتصدر إرشادات تشغيلية محدثة','low','AE'),
 ('palestine_israel','تحديث إضافي حول المفاوضات والوضع الإنساني والتحركات الميدانية في غزة','high','PS'),
 ('jordan','عمّان تكثف التنسيق مع الشركاء الإقليميين بشأن الحدود والمساعدات','medium','JO'),
]

def event(region,title,severity,country,index,long=False):
    summary=SUMMARY.get(region,'ملخص اصطناعي موجز لاختبار تصميم النشرة وليس خبراً حقيقياً.')
    assessment='يتطلب التطور متابعة المؤشرات الرسمية والميدانية قبل استخلاص أثر نهائي.'
    watch='متابعة البيانات الرسمية وأي تغير موثق في الإجراءات أو المواقف.'
    if long:
        title+=' مع استمرار الاتصالات وتباين المواقف الرسمية وارتفاع الحاجة إلى متابعة المؤشرات الميدانية خلال الساعات المقبلة'
        summary+=' ويضيف هذا المثال نصاً أطول لاختبار التفاف العربية وتباعد السطور ومنع أي تداخل بين العناصر.'
    return dict(region=region,topic='security',title_ar=title,summary_ar=summary,assessment_ar=assessment,
      watch_ar=watch,severity=severity,status_ar='تقرير منسوب',fingerprint='sample-'+str(index),
      source_ids=['sample-'+str(index)],sources=[dict(id='sample-'+str(index),source='مصدر تجريبي — ليس مصدراً إخبارياً',
      url='https://example.com/synthetic/'+str(index),published=0,affiliation='synthetic',kind='news',country=country)])

def fixture(long=False):
    start,end=edition_window(datetime.now(timezone.utc)); events=[]
    countries={'gcc':'AE','iran':'IR','turkey':'TR','iraq':'IQ','yemen':'YE','sudan':'SD','sahel':'ML',
      'north_africa':'DZ','egypt':'EG','oman':'OM','pakistan':'PK','afghanistan':'AF','horn':'ET','somalia':'SO','levant':'LB','palestine_israel':'PS','jordan':'JO'}
    for i,region in enumerate(REGIONS):
        sev='high' if region in ('palestine_israel','iran','yemen','sudan') else 'medium'
        e=event(region,BASE[region],sev,countries[region],i,long); e['sources'][0]['published']=end.timestamp()-600; events.append(e)
    for j,(region,title,sev,country) in enumerate(EXTRA,len(events)):
        e=event(region,title,sev,country,j,long); e['sources'][0]['published']=end.timestamp()-900; events.append(e)
    analysis={
      'situation_ar':'تُظهر العينة تزامن مسارات دبلوماسية وأمنية متعددة من دون افتراض رابط سببي بينها. ويظل الأهم لصانع القرار هو التمييز بين الرسائل السياسية والإجراءات التنفيذية القابلة للرصد.',
      'implications_ar':'أي تغير موثق في الانتشار أو القيود التشغيلية أو ترتيبات الحدود أو الممرات البحرية قد يغيّر قراءة المشهد أكثر من تكرار التصريحات.',
      'developing_ar':[
        'مسار التهدئة في غزة بين التفاوض والوصول الإنساني وإيقاع التطورات الميدانية.',
        'أمن البحر الأحمر والممرات البحرية مع مراقبة أي قيود تشغيلية أو تحركات أمنية جديدة.',
        'الحدود العراقية والسورية وتحركات الفصائل والاتصالات الرسمية ذات الصلة.',
        'السودان والقرن الأفريقي وتأثير التطورات الميدانية على الاستقرار والوصول الإنساني.'
      ],
      'watch_ar':[
        'أي إعلان رسمي يغيّر شروط التهدئة أو آليات المساعدات.',
        'أي تقييد موثق في مجال جوي أو ممر بحري مهم.',
        'الانتقال من التصريحات إلى إجراءات عسكرية أو أمنية قابلة للرصد.',
        'بيانات أو اجتماعات رسمية تعكس تنسيقاً إقليمياً جديداً.'
      ]
    }
    coverage={'event_source_count':len(events),'non_arabic_event_sources':6,
              'event_source_languages':{'ar':max(1,len(events)-6),'en':4,'fa':1,'tr':1}}
    return dict(sample=True,window_start=start.isoformat(),window_end=end.isoformat(),events=events,input_count=84,
      health=[dict(id='sample-'+r,name='مصدر تجريبي',region=r,country='SAMPLE',status='active') for r in REGIONS],
      analysis=analysis,coverage=coverage,previous_events=[{'title_ar':events[0]['title_ar']}])
