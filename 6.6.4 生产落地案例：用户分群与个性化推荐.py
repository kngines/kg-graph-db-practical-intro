from py2neo import Graph
import networkx as nx
import community as community_louvain
import json


def create_sample_data():
    """创建样例数据，确保用户之间有共同购买的商品"""
    graph = Graph("bolt://localhost:7687", user="neo4j", password="123456")

    # 清空现有数据
    graph.run("MATCH (n) DETACH DELETE n")

    # 创建用户节点
    users_data = [
        {"id": "U10086", "name": "用户1"},
        {"id": "U10087", "name": "用户2"},
        {"id": "U10088", "name": "用户3"},
        {"id": "U10089", "name": "用户4"},
        {"id": "U10090", "name": "用户5"},
    ]
    for user in users_data:
        graph.run("CREATE (u:User {id: $id, name: $name})", id=user["id"], name=user["name"])

    # 创建商品节点
    items_data = [
        {"id": "I001", "name": "商品1", "category": "电子产品"},
        {"id": "I002", "name": "商品2", "category": "服装"},
        {"id": "I003", "name": "商品3", "category": "食品"},
        {"id": "I004", "name": "商品4", "category": "图书"},
        {"id": "I005", "name": "商品5", "category": "家居"},
        {"id": "I006", "name": "商品6", "category": "电子产品"},  # 新增商品
        {"id": "I007", "name": "商品7", "category": "服装"},  # 新增商品
    ]
    for item in items_data:
        graph.run("CREATE (i:Item {id: $id, name: $name, category: $category})",
                  id=item["id"], name=item["name"], category=item["category"])

    # 创建购买关系 - 优化数据结构，确保有推荐候选
    buy_relations = [
        # U10086 的购买
        {"user_id": "U10086", "item_id": "I001", "amount": 1000},
        {"user_id": "U10086", "item_id": "I002", "amount": 200},
        {"user_id": "U10086", "item_id": "I004", "amount": 75},

        # U10087 的购买（与U10086有共同购买）
        {"user_id": "U10087", "item_id": "I001", "amount": 800},  # 共同购买I001
        {"user_id": "U10087", "item_id": "I003", "amount": 150},
        {"user_id": "U10087", "item_id": "I005", "amount": 400},
        {"user_id": "U10087", "item_id": "I006", "amount": 600},  # U10087独有

        # U10088 的购买（与U10086有共同购买）
        {"user_id": "U10088", "item_id": "I002", "amount": 300},  # 共同购买I002
        {"user_id": "U10088", "item_id": "I004", "amount": 80},  # 共同购买I004
        {"user_id": "U10088", "item_id": "I007", "amount": 250},  # U10088独有

        # U10089 的购买
        {"user_id": "U10089", "item_id": "I003", "amount": 120},
        {"user_id": "U10089", "item_id": "I005", "amount": 500},
        {"user_id": "U10089", "item_id": "I006", "amount": 300},  # U10089独有

        # U10090 的购买（与U10086有共同购买）
        {"user_id": "U10090", "item_id": "I001", "amount": 1200},  # 共同购买I001
        {"user_id": "U10090", "item_id": "I004", "amount": 90},  # 共同购买I004
        {"user_id": "U10090", "item_id": "I007", "amount": 180},  # U10090独有
    ]

    for relation in buy_relations:
        graph.run("""
        MATCH (u:User {id: $user_id}), (i:Item {id: $item_id})
        CREATE (u)-[:BUY {amount: $amount}]->(i)
        """, user_id=relation["user_id"], item_id=relation["item_id"], amount=relation["amount"])

    print(f"成功创建{len(users_data)}个用户，{len(items_data)}个商品，{len(buy_relations)}个购买关系")


def user_recommendation_pipeline(user_id="U10086"):
    # 首先创建样例数据
    create_sample_data()

    # 1. 连接Neo4j
    graph = Graph("bolt://localhost:7687", user="neo4j", password="123456")

    # 2. 构建业务图（用户-商品-订单）
    def build_business_graph():
        G = nx.Graph()
        # 读取用户节点
        users_df = graph.run("MATCH (n:User) RETURN n.id AS id").to_data_frame()
        if not users_df.empty and 'id' in users_df.columns:
            G.add_nodes_from(users_df["id"].dropna().tolist(), type="user")

        # 读取商品节点
        items_df = graph.run("MATCH (n:Item) RETURN n.id AS id, n.category AS category").to_data_frame()
        if not items_df.empty and all(col in items_df.columns for col in ['id', 'category']):
            for _, row in items_df.iterrows():
                if row["id"] is not None and row["category"] is not None:
                    G.add_node(row["id"], type="item", category=row["category"])

        # 读取购买关系
        buy_edges_df = graph.run("""
        MATCH (u:User)-[r:BUY]->(i:Item)
        RETURN u.id AS user, i.id AS item, r.amount AS amount
        """).to_data_frame()

        # 验证边数据并添加到图中
        if not buy_edges_df.empty and all(col in buy_edges_df.columns for col in ['user', 'item', 'amount']):
            # 过滤掉 None 值
            valid_edges_df = buy_edges_df.dropna(subset=['user', 'item', 'amount'])
            if not valid_edges_df.empty:
                edges = valid_edges_df[["user", "item", "amount"]].values.tolist()
                G.add_weighted_edges_from(edges)

        return G

    G = build_business_graph()

    # 验证图是否包含必要的节点和边
    if G.number_of_nodes() == 0:
        print("警告：图中没有节点，无法进行推荐")
        return []
    if G.number_of_edges() == 0:
        print("警告：图中没有边，无法进行推荐")
        return []

    # 检查目标用户是否存在
    if user_id not in G.nodes():
        print(f"警告：用户 {user_id} 不存在于图中")
        return []

    # 3. 社区发现（用户分群）
    # 投影用户网络（基于共同购买商品）
    user_nodes = [n for n in G.nodes() if G.nodes[n]["type"] == "user"]
    if len(user_nodes) < 2:
        print("警告：用户节点不足，无法进行社区发现")
        return []

    user_graph = nx.bipartite.projection.projected_graph(G, user_nodes)

    if user_graph.number_of_nodes() > 0 and user_graph.number_of_edges() > 0:
        louvain_partition = community_louvain.best_partition(user_graph, weight="weight")

        # 调试输出社区划分结果
        print(f"社区划分结果: {louvain_partition}")
    else:
        print("警告：用户子图为空，无法进行社区发现")
        return []

    # 4. 同社区商品推荐（基于Adamic-Adar指数）
    # 获取目标用户所在社区
    if user_id not in louvain_partition:
        print(f"警告：用户 {user_id} 不在社区划分结果中")
        return []

    target_community = louvain_partition[user_id]
    # 获取同社区其他用户
    community_users = [u for u, cid in louvain_partition.items() if cid == target_community and u != user_id]
    print(f"同社区用户: {community_users}")

    # 获取目标用户已购买商品
    bought_items = [n for n in G.neighbors(user_id) if G.nodes[n]["type"] == "item"]
    print(f"{user_id} 已购买商品: {bought_items}")

    # 待推荐商品：同社区用户购买过但目标用户未购买的商品
    candidate_items = []
    for u in community_users:
        u_bought = [n for n in G.neighbors(u) if G.nodes[n]["type"] == "item"]
        print(f"用户 {u} 购买商品: {u_bought}")
        candidate_items.extend([item for item in u_bought if item not in bought_items])
    candidate_items = list(set(candidate_items))  # 去重
    print(f"候选推荐商品: {candidate_items}")

    if not candidate_items:
        print(f"警告：没有找到可推荐的商品给用户 {user_id}")
        return []

    # 计算推荐分数（Adamic-Adar指数）
    candidate_pairs = [(user_id, item) for item in candidate_items]
    recommendations = []
    try:
        for u, item, score in nx.algorithms.link_prediction.adamic_adar_index(G, candidate_pairs):
            if item in G.nodes and 'category' in G.nodes[item]:
                recommendations.append({
                    "item_id": item,
                    "category": G.nodes[item]["category"],
                    "prediction_score": round(score, 4)
                })
    except Exception as e:
        print(f"计算推荐分数时出错: {e}")
        return []

    # 按分数排序，取Top10
    recommendations = sorted(recommendations, key=lambda x: x["prediction_score"], reverse=True)[:10]

    # 5. 推荐结果回写Neo4j - 修复属性类型错误
    # 将推荐结果转换为JSON字符串以适应Neo4j属性要求
    recommendations_json = json.dumps(recommendations, ensure_ascii=False)
    graph.run("""
    MATCH (u:User {id: $user_id})
    SET u.recommendations = $recommendations, u.recommend_time = datetime()
    """, user_id=user_id, recommendations=recommendations_json)

    print(f"为用户{user_id}生成{len(recommendations)}条推荐商品")
    return recommendations


# 执行推荐流程
user_recommendation_pipeline(user_id="U10086")
