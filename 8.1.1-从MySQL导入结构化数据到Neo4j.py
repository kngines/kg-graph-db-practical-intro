# 环境准备：pip install neo4j sqlalchemy pymysql pandas
import pandas as pd
from neo4j import GraphDatabase
from sqlalchemy import create_engine

# 1. 配置数据库连接
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "company_db"
}
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687"
}

# 创建 SQLAlchemy 引擎
def create_mysql_engine():
    connection_string = f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}/{MYSQL_CONFIG['database']}"
    return create_engine(connection_string)


# 2. 从MySQL读取结构化数据
def read_mysql_data():
    engine = create_mysql_engine()
    # 读取员工表和部门表
    df_employee = pd.read_sql("SELECT id, name, age, dept_id FROM employee", engine)
    df_department = pd.read_sql("SELECT id, name, location FROM department", engine)
    engine.dispose()  # 关闭连接
    return df_employee, df_department


# 3. 导入Neo4j
def import_to_neo4j(df_employee, df_department):
    driver = GraphDatabase.driver(**NEO4J_CONFIG)

    # 写入部门节点
    with driver.session() as session:
        for _, row in df_department.iterrows():
            session.run("""
                MERGE (d:Department {id: $id, name: $name, location: $location})
            """, id=row["id"], name=row["name"], location=row["location"])

    # 写入员工节点 + 员工-部门关系
    with driver.session() as session:
        for _, row in df_employee.iterrows():
            session.run("""
                MERGE (e:Employee {id: $id, name: $name, age: $age})
                MERGE (d:Department {id: $dept_id})
                MERGE (e)-[:WORKS_IN]->(d)
            """, id=row["id"], name=row["name"], age=row["age"], dept_id=row["dept_id"])

    driver.close()
    print("结构化数据导入Neo4j完成！")


# 执行导入
df_emp, df_dept = read_mysql_data()
import_to_neo4j(df_emp, df_dept)
