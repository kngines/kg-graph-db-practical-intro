from neo4j import GraphDatabase


# 1. 连接Neo4j数据库
class Neo4jClient:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    # 2. 创建节点（用户节点和商品节点）
    def create_nodes(self):
        with self.driver.session() as session:
            # 创建用户节点
            session.run("""
                CREATE (u1:User {id: 1, name: "张三", age: 25, city: "北京"})
                CREATE (u2:User {id: 2, name: "李四", age: 30, city: "上海"})
                CREATE (g1:Goods {id: 101, name: "智能手机", price: 4999, category: "数码产品"})
                CREATE (g2:Goods {id: 102, name: "无线耳机", price: 799, category: "数码配件"})
            """)
            print("节点创建成功！")

    # 3. 创建关系（用户-购买-商品）
    def create_relationships(self):
        with self.driver.session() as session:
            # 分别执行每个关系创建操作
            session.run("""
                MATCH (u:User {id: 1}), (g:Goods {id: 101})
                CREATE (u)-[r:BUY {buy_time: "2025-12-01", amount: 1, payment: "微信"}]->(g)
            """)

            session.run("""
                MATCH (u:User {id: 1}), (g:Goods {id: 102})
                CREATE (u)-[r:BUY {buy_time: "2025-12-05", amount: 2, payment: "支付宝"}]->(g)
            """)

            session.run("""
                MATCH (u:User {id: 2}), (g:Goods {id: 101})
                CREATE (u)-[r:BUY {buy_time: "2025-12-03", amount: 1, payment: "银行卡"}]->(g)
            """)
            print("关系创建成功！")

    # 4. 查询数据（查询张三购买的所有商品）
    def query_data(self):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {name: "张三"})-[r:BUY]->(g:Goods)
                RETURN u.name, r.buy_time, g.name, g.price, r.amount
            """)
            for record in result:
                print(f"用户：{record['u.name']}")
                print(f"购买时间：{record['r.buy_time']}")
                print(f"商品名称：{record['g.name']}")
                print(f"商品价格：{record['g.price']}")
                print(f"购买数量：{record['r.amount']}")
                print("-" * 20)

    # 5. 更新数据（修改无线耳机的价格）
    def update_data(self):
        with self.driver.session() as session:
            session.run("""
                MATCH (g:Goods {name: "无线耳机"})
                SET g.price = 699, g.update_time = "2025-12-22"
            """)
            print("数据更新成功！")

    # 6. 删除数据（删除李四购买智能手机的关系）
    def delete_data(self):
        with self.driver.session() as session:
            session.run("""
                MATCH (u:User {name: "李四"})-[r:BUY]->(g:Goods {name: "智能手机"})
                DELETE r
            """)
            print("关系删除成功！")


# 执行主流程
if __name__ == "__main__":
    client = Neo4jClient("bolt://localhost:7687", "root", "root")
    try:
        client.create_nodes()
        client.create_relationships()
        client.query_data()
        client.update_data()
        client.delete_data()
    finally:
        client.close()