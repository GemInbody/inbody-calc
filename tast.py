import datetime
import requests
import pandas as pd
import plotly.express as px
import streamlit as st

# 1. إعدادات الصفحة
st.set_page_config(
    page_title="Smart Farmer Assistant", page_icon="🌾", layout="wide"
)

st.title("🌾 Smart Farmer Assistant")
st.caption(
    "Field Shift: Adapting Farms with NASA Data | SMART STEM • NASA SPACE APPS 2026"
)
st.markdown("---")

# 2. القائمة الجانبية لإدخال البيانات من المزارع
st.sidebar.header("📋 بيانات المزرعة والموقع")

# اختيار المحصول
crop = st.sidebar.selectbox(
    "اختر المحصول الزراعي:",
    ["القمح", "الذرة", "الطماطم"],
    help="تختلف حدود التحمل الحراري بحسب المحصول المختارات",
)

# تحديد الإحداثيات (افتراضيًا موقع تجريبي في مصر)
lat = st.sidebar.number_input(
    "خط العرض (Latitude):", value=30.0444, format="%.4f"
)
lon = st.sidebar.number_input(
    "خط الطول (Longitude):", value=31.2357, format="%.4f"
)

# نطاق التواريخ (آخر 30 يوم لضمان وجود بيانات جديدة)
end_date = datetime.date.today() - datetime.timedelta(days=2)
start_date = end_date - datetime.timedelta(days=30)


# 3. دالة لجلب البيانات من NASA POWER API
@st.cache_data(ttl=3600)
def fetch_nasa_data(latitude, longitude, start, end):
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "T2M,PRECTOTCORR",  # درجة الحرارة والأمطار اليومية
        "community": "AG",
        "longitude": longitude,
        "latitude": latitude,
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": "JSON",
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            properties = data["properties"]["parameter"]

            df_temp = pd.DataFrame(
                list(properties["T2M"].items()), columns=["Date", "Temperature"]
            )
            df_precip = pd.DataFrame(
                list(properties["PRECTOTCORR"].items()),
                columns=["Date", "Precipitation"],
            )

            df = pd.merge(df_temp, df_precip, on="Date")
            df["Date"] = pd.to_datetime(df["Date"], format="%Y%m%d")
            return df
        else:
            return None
    except Exception as e:
        return None


# 4. معالجة البيانات وتحليل الإجهاد الحراري
df_data = fetch_nasa_data(lat, lon, start_date, end_date)

if df_data is not None and not df_data.empty:
    # حدود الحرارة الحرجة للمحاصيل (أمثلة مرجعية بسيطة)
    thresholds = {"القمح": 30.0, "الذرة": 35.0, "الطماطم": 32.0}
    temp_limit = thresholds[crop]

    # حساب الإحصائيات
    max_temp = df_data["Temperature"].max()
    avg_temp = df_data["Temperature"].mean()
    total_precip = df_data["Precipitation"].sum()
    heat_stress_days = df_data[df_data["Temperature"] > temp_limit]

    # عرض كروت المؤشرات السريعة (Metrics)
    col1, col2, col3 = st.columns(3)
    col1.metric("أعلى درجة حرارة", f"{max_temp:.1f} °C")
    col2.metric("متوسط درجة الحرارة", f"{avg_temp:.1f} °C")
    col3.metric("إجمالي الأمطار", f"{total_precip:.1f} mm")

    st.markdown("---")

    # 5. عرض حالة الموسم والتنبيهات
    st.subheader("🚨 حالة الموسم الزراعي والتنبيهات")

    if not heat_stress_days.empty:
        st.error(
            f"⚠️ تحذير إجهاد حراري: تم تسجيل {len(heat_stress_days)} أيام تجاوزت فيها درجة الحرارة الحد المسموح لـ ({crop}) وهي {temp_limit}°C."
        )
    else:
        st.success(
            f"✅ الظروف ملائمة: درجات الحرارة ضمن المعدل الطبيعي لنمو محصول ({crop})."
        )

    if total_precip < 5.0:
        st.warning(
            "⚠️ نقص في هطول الأمطار: معدل الأمطار منخفض خلال الفترة المحددة، يُرجى مراقبة جفاف التربة."
        )

    # 6. الرسوم البيانية للتغيرات الجوية
    st.markdown("---")
    st.subheader("📊 تحليل تغيرات الحرارة والأمطار")

    # رسم بياني للحرارة
    fig_temp = px.line(
        df_data,
        x="Date",
        y="Temperature",
        title=f"تغير درجات الحرارة اليومية (°C) - الحد الخطر لـ {crop}: {temp_limit}°C",
        labels={"Date": "التاريخ", "Temperature": "درجة الحرارة (°C)"},
        markers=True,
    )
    # إضافة خط أفقي للحد الخطر
    fig_temp.add_hline(
        y=temp_limit,
        line_dash="dash",
        line_color="red",
        annotation_text="حد الإجهاد الحراري",
    )
    st.plotly_chart(fig_temp, use_container_width=True)

    # رسم بياني للأمطار
    fig_precip = px.bar(
        df_data,
        x="Date",
        y="Precipitation",
        title="معدل هطول الأمطار اليومي (mm)",
        labels={"Date": "التاريخ", "Precipitation": "الأمطار (mm)"},
        color_discrete_sequence=["#1f77b4"],
    )
    st.plotly_chart(fig_precip, use_container_width=True)

    # 7. النصائح والإرشادات المرجعية
    st.markdown("---")
    st.subheader("💡 نصائح وإرشادات عامة")
    st.info(
        f"""
    - تظليل وتبريد: في أيام الإجهاد الحراري التي تتجاوز {temp_limit}°C، يُنصح بتوفير وسائل تظليل خفيفة إن أمكن للحد من النتح الزائد.
    - مواعيد العمل: يفضل إجراء العمليات الزراعية والحقلية في ساعات الصباح الباكر أو المساء لتجنب إجهاد النبات.
    - ملاحظة: هذه التوجيهات استرشادية بناءً على البيانات المناخية وليست توصيات ري تفصيلية.
    """
    )

else:
    st.error(
        "تعذر جلب البيانات من NASA POWER حالياً، يُرجى التأكد من الإحداثيات أو محاولة التحديث."
    )