"""Synthetic Arabic fixture. Never used as a live fallback."""
from datetime import datetime, timezone
from .core import REGIONS, edition_window

TITLES=[
'محادثات إقليمية لخفض التصعيد وتأمين الممرات البحرية',
'متابعة التصريحات بشأن النشاط العسكري قرب الحدود',
'جهود دبلوماسية لاستئناف الحوار حول ترتيبات الأمن الإقليمي',
'تقارير محلية عن مراجعة الإجراءات الأمنية في المناطق الحدودية',
'دعوات إلى تثبيت وقف إطلاق النار وتسهيل وصول المساعدات',
'وسطاء يطالبون بحماية المدنيين وفتح ممرات إنسانية آمنة',
'متابعة التعاون الأمني والتطورات السياسية في منطقة الساحل',
'مشاورات حول الاستقرار الإقليمي وأمن البنية التحتية',
'تصريحات رسمية بشأن التنسيق الأمني ومكافحة العنف',
'متابعة الأوضاع الحدودية وتطورات الاتصالات الدبلوماسية',
'جهود إقليمية لتعزيز أمن الملاحة وخفض التوتر',
'متابعة المساعي الدبلوماسية وحماية المدنيين في بلاد الشام']

def fixture(long=False):
    start,end=edition_window(datetime.now(timezone.utc)); events=[]
    for i,region in enumerate(REGIONS):
        title=TITLES[i]
        summary='هذا نص اصطناعي لاختبار التصميم وليس خبراً حقيقياً. ينسب الملخص التطور إلى مصدره ويحافظ على حدود المعلومات المتاحة دون تحويل الادعاءات إلى وقائع مؤكدة.'
        if long:
            title+=' في ظل استمرار المشاورات وتباين المواقف الرسمية بشأن الخطوات المقبلة وآليات المتابعة المشتركة'
            summary+=' ويختبر هذا المثال الطويل التفاف الأسطر العربية والتباعد بين الفقرات وعلامات الترقيم والأسماء المختلطة دون تداخل النص مع حدود الأقسام.'
        events.append(dict(region=region,topic='security',title_ar=title,summary_ar=summary,
          assessment_ar='قد تسهم الاتصالات في توضيح المواقف؛ ولا تكفي البيانات المتاحة لاستنتاج تغير ميداني مؤكد.',
          watch_ar='متابعة البيانات اللاحقة والتحقق من اتساق التقارير المحلية.',severity='high' if i<3 else 'medium' if i<8 else 'low',
          status_ar='تقرير منسوب',fingerprint='sample-'+str(i),source_ids=['sample-'+str(i)],
          sources=[dict(id='sample-'+str(i),source='مصدر تجريبي — ليس مصدراً إخبارياً',url='https://example.com/synthetic/'+str(i),
            published=end.timestamp()-600,affiliation='synthetic',kind='social' if i==3 else 'news')]))
    return dict(sample=True,window_start=start.isoformat(),window_end=end.isoformat(),events=events,input_count=36,
      health=[dict(id='sample-'+r,name='مصدر تجريبي',region=r,country='SAMPLE',status='active') for r in REGIONS])
