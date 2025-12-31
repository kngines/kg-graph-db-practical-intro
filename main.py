from mongoengine import connect, Document, EmbeddedDocument, StringField, IntField, FloatField, ListField, EmbeddedDocumentField, ReferenceField, ObjectIdField

# 连接MongoDB
connect(
    db="student_course_db",
    host="localhost",
    port=27017,
    alias="default"
)

# -------------------------- 方式1：内嵌文档 --------------------------
class CourseEmbedded(EmbeddedDocument):
    course_name = StringField(required=True)
    teacher = StringField(required=True)
    credit = IntField(required=True)
    score = FloatField(required=True)

class Student(Document):
    student_name = StringField(required=True)
    age = IntField(required=True)
    gender = StringField(required=True)
    courses = ListField(EmbeddedDocumentField(CourseEmbedded))
    meta = {"collection": "students"}

# 插入张三数据
try:
    zhangsan = Student(
        student_name="张三",
        age=20,
        gender="男",
        courses=[
            CourseEmbedded(course_name="数据库原理", teacher="王老师", credit=3, score=85.5),
            CourseEmbedded(course_name="人工智能", teacher="李老师", credit=4, score=92.0)
        ]
    )
    zhangsan.save()
    print("张三数据插入成功")
except Exception as e:
    print(f"插入张三数据异常：{e}")

# 查询张三课程
try:
    student = Student.objects(student_name="张三").first()
    if student:
        print("张三的所有课程：")
        for course in student.courses:
            print(f"课程名：{course.course_name}，老师：{course.teacher}，学分：{course.credit}，成绩：{course.score}")
    else:
        print("未找到张三的信息")
except Exception as e:
    print(f"查询张三数据异常：{e}")

# -------------------------- 方式2：文档引用 --------------------------
class Course(Document):
    course_name = StringField(required=True)
    teacher = StringField(required=True)
    credit = IntField(required=True)
    meta = {"collection": "courses"}

class ScoreEmbedded(EmbeddedDocument):
    course_id = ObjectIdField(required=True)
    score = FloatField(required=True)

class StudentRef(Document):
    student_name = StringField(required=True)
    age = IntField(required=True)
    gender = StringField(required=True)
    course_ids = ListField(ReferenceField(Course))
    scores = ListField(EmbeddedDocumentField(ScoreEmbedded))
    meta = {"collection": "student_refs"}

# 插入课程数据
try:
    db_course = Course(course_name="数据库原理", teacher="王老师", credit=3)
    db_course.save()
    ai_course = Course(course_name="人工智能", teacher="李老师", credit=4)
    ai_course.save()
    print("课程数据插入成功")
except Exception as e:
    print(f"插入课程数据异常：{e}")

# 插入李四数据
try:
    lisi = StudentRef(
        student_name="李四",
        age=21,
        gender="女",
        course_ids=[db_course.id, ai_course.id],
        scores=[ScoreEmbedded(course_id=db_course.id, score=78.0)]
    )
    lisi.save()
    print("李四数据插入成功")
except Exception as e:
    print(f"插入李四数据异常：{e}")

# 修正后的查询李四数据（使用 prefetch_related 实现关联查询）
try:
    student = StudentRef.objects(student_name="李四").first()
    if student:
        print("\n李四的信息及关联课程：")
        print(f"姓名：{student.student_name}，年龄：{student.age}，性别：{student.gender}")
        print("所选课程：")
        # 手动获取引用的课程对象
        courses = Course.objects(id__in=[course.id for course in student.course_ids])
        course_dict = {str(course.id): course for course in courses}

        for course_ref in student.course_ids:
            course = course_dict.get(str(course_ref.id))
            if course:
                print(f"课程名：{course.course_name}，老师：{course.teacher}，学分：{course.credit}")

        print("成绩信息：")
        for score_info in student.scores:
            course = Course.objects(id=score_info.course_id).first()
            if course:
                print(f"课程：{course.course_name}，成绩：{score_info.score}")
    else:
        print("未找到李四的信息")
except Exception as e:
    print(f"查询李四数据异常：{e}")