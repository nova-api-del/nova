# قناة قصص البقاء المرسومة (إنجليزي) — خط الإنتاج

**المسار:** Groq يكتب قصة أصلية ← Z-Image Turbo يرسم المشاهد ← Edge TTS صوت إنجليزي ← FFmpeg يجمع (1080p + ترجمة) ← رفع اختياري إلى يوتيوب ← تحليلات يومية تغذّي القصص الجديدة.

## ما تحتاجه (كله مجاني)
1. **Groq API key:** console.groq.com ← API Keys. أضفه في Kaggle Secrets باسم `GROQ_API_KEY`.
2. **شخصيتك الخاصة:** عدّل `data/story_channel/character.json` (الاسم والشكل والأسلوب). لا تنسخ شخصيات قنوات أخرى.
3. **تشغيل:** افتح `notebooks/nova-story-channel-kaggle.ipynb` في Kaggle (GPU + Internet) ← Run All.

## ربط يوتيوب (للرفع وقراءة الإحصائيات)
1. في Google Cloud: أنشئ مشروعاً وفعّل **YouTube Data API v3** و**YouTube Analytics API**، ثم أنشئ OAuth Client من نوع **Web application** وأضف Redirect URI: `https://developers.google.com/oauthplayground`
2. شاشة الموافقة: اجعل الحالة **In production** (في وضع Testing ينتهي الـ refresh token بعد 7 أيام).
3. من developers.google.com/oauthplayground: اضغط الترس ← فعّل *Use your own OAuth credentials* وأدخل Client ID وSecret، ثم اطلب هذه الصلاحيات:
   `https://www.googleapis.com/auth/youtube.upload` و `https://www.googleapis.com/auth/youtube.readonly` و `https://www.googleapis.com/auth/yt-analytics.readonly`
   ثم سجّل الدخول بحساب القناة واضغط Exchange authorization code وانسخ **Refresh token**.
4. أضف الأسرار `YT_CLIENT_ID` و`YT_CLIENT_SECRET` و`YT_REFRESH_TOKEN` في **Kaggle Secrets** (للرفع) وفي **GitHub ← Settings ← Secrets ← Actions** (للتحليلات).

**تنبيهات مهمة:**
- مشاريع API غير الموثّقة تُقفل فيها الفيديوهات المرفوعة على **Private** حتى تجتاز "API Compliance Audit" من جوجل. إن ظهرت فيديوهاتك Private رغم طلبك Public فهذا هو السبب؛ يمكنك النشر يدوياً من YouTube Studio.
- حصة الـ API اليومية 10,000 وحدة ورفع الفيديو يكلف 1,600، أي نحو 6 رفعات يومياً كحد أقصى.
- الرفع يضع علامة "محتوى اصطناعي" افتراضياً (`YT_SYNTHETIC=true`) لأن الصوت مولّد بالذكاء الاصطناعي.
- الصور المخصصة (Thumbnails) تحتاج قناة موثّقة برقم الهاتف.

## حلقة التعلّم
وركفلو **Channel Analytics** يعمل يومياً، يسحب المشاهدات ونسبة المشاهدة لكل فيديو ويكتبها في `data/story_channel/insights.json`. سكربت القصة يقرأ أفضل 5 فيديوهات ويتعلم نمطها ويتجنب تكرار العناوين.
