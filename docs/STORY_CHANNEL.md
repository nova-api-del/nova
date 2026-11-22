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
- حصة الـ API اليومية الافتراضية 10,000 وحدة. كان رفع الفيديو يكلف 1,600 وحدة، لكن مقالاً حديثاً يذكر أنه نزل إلى نحو 100. تحقق من الرقم الفعلي في Google Cloud ← APIs & Services ← Quotas قبل أن تعتمد على عدد الرفعات اليومية.
- الرفع يضع علامة "محتوى اصطناعي" افتراضياً (`YT_SYNTHETIC=true`) لأن الصوت مولّد بالذكاء الاصطناعي.
- الصور المخصصة (Thumbnails) تحتاج قناة موثّقة برقم الهاتف.

## حلقة التعلّم
وركفلو **Channel Analytics** يعمل يومياً، يسحب المشاهدات ونسبة المشاهدة لكل فيديو ويكتبها في `data/story_channel/insights.json`. سكربت القصة يقرأ أفضل 5 فيديوهات ويتعلم نمطها ويتجنب تكرار العناوين.


## تحريك المشاهد المهمة بـ Wan 2.2 (اختياري، افتراضياً مغلق)
- الأساس يبقى صوراً ثابتة بحركة كاميرا (مجاني وسريع). نموذج **Wan 2.2 (TI2V-5B)** مفتوح المصدر بترخيص Apache 2.0 ويسمح بالاستخدام التجاري، ويحرّك من 3 إلى 5 مشاهد فقط في كل فيديو.
- كاتب القصة يعلّم 5 مشاهد بـ `key_moment` (المقدمة، أول خطر، نقطة التحول، الذروة، النهاية). والمشاهد تُختار تلقائياً من `scripts/story_channel/animate_plan.py`.
- في الدفتر غيّر `ANIMATE = True` في الخلية 2b. يُنتج كل مشهد ملف `scene_NN.mp4`، ويستخدمه الرندر بدل الصورة، ويكرره ذهاباً وإياباً (ping-pong) حتى تنتهي جملة التعليق بلا قفزة.
- **غير مجرَّب على Kaggle.** لم أستطع تشغيل النموذج من بيئتي. إن فشل مشهد يبقى صورة ثابتة ولا يتوقف البناء. وإن ظهر خطأ نقص ذاكرة قلّل `num_frames` إلى 33 أو `MAX_ANIMATED` إلى 3. بطاقات T4 لا تدعم bf16 فقد يكون التوليد بطيئاً أو غير مستقر.
- ما فُحص فعلاً: اختيار المشاهد، ودمج مقطع محرّك مع الصوت والترجمة بـ FFmpeg (اختبارات في `tests/test_story_channel.py`).

## تراخيص الأصوات (مهم للربح)
- **لا تستخدم XTTS v2** (ترخيص CPML غير تجاري) **ولا F5-TTS** (CC-BY-NC) في فيديوهات مربحة.
- بدائل بتراخيص تجارية: **Kokoro-82M** (Apache 2.0) و**Chatterbox** (MIT).
- الرندر الحالي يستخدم Edge TTS لأنه مجاني وبلا مفتاح ويعطي توقيت الكلمات للترجمة. هو خدمة غير رسمية وقد تتغير شروطها أو تتوقف، فراجع هذا قبل الاعتماد عليه.

## أدوات مفتوحة المصدر نظرتُ فيها
| الأداة | القرار |
|---|---|
| Wan 2.2 | مُضاف (اختياري) |
| CogVideoX-2B | بديل Apache 2.0، لم يُضف |
| HunyuanVideo 1.5 | ترخيص Tencent Community، لم يُضف |
| LTX-2.3 | ترخيصه مشروط بالإيراد وذاكرته أكبر، لم يُضف |
| Wan2GP | واجهة لتشغيل نماذج كثيرة على بطاقات ضعيفة، محلي فقط حسب مصدره، لم يُضف |
| MoneyPrinterTurbo | لقطات مخزّنة لفيديوهات قصيرة، لا يناسب قصصاً طويلة |
