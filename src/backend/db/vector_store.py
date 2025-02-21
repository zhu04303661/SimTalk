from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from ..providers.azure_openai import azure_openai
import time
import backoff  # 需要安装: pip install backoff

class ModelicaVectorStore:
    def __init__(self, persist_directory: Optional[str] = None):
        """初始化向量数据库
        
        Args:
            persist_directory: 持久化存储目录，如果为None则使用内存存储
        """
        # 初始化ChromaDB客户端
        chroma_settings = Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ) if persist_directory else Settings(anonymized_telemetry=False)
        
        self.chroma_client = chromadb.Client(chroma_settings)
        self.collection = self.chroma_client.get_or_create_collection(
            name="modelica_examples",
            metadata={"description": "Modelica示例代码库"}
        )

    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=5,
        max_time=30
    )
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """获取文本的embedding向量"""
        try:
            # 确保文本不为空
            if not text or not text.strip():
                return None
            import ipdb
            #ipdb.set_trace()    
            return azure_openai.get_embedding(text)
        except Exception as e:
            print(f"获取embedding失败: {str(e)}")
            raise  # 让backoff处理重试

    def add_examples(self, examples: Dict[str, Dict]):
        """批量添加示例到向量数据库
        
        Args:
            examples: 示例字典，格式为 {
                "name": {
                    "description": str,
                    "keywords": List[str],
                    "code": str,
                    "model_name": str
                }
            }
        """
        embeddings = []
        documents = []
        metadatas = []
        ids = []
        
        for name, example in examples.items():
            # 合并描述和关键词作为文本
            text = f"{example['description']} {' '.join(example['keywords'])}"
            embedding = self._get_embedding(text)
            
            if embedding:
                embeddings.append(embedding)
                documents.append(example["code"])
                metadatas.append({
                    "description": example["description"],
                    "model_name": example.get("model_name", ""),
                    "keywords": ",".join(example["keywords"])
                })
                ids.append(name)
        
        if embeddings:
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

    def search(self, query: str, n_results: int = 1, 
               similarity_threshold: float = 0.3) -> List[Dict]:
        """搜索最相似的示例代码
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            similarity_threshold: 相似度阈值
            
        Returns:
            匹配的示例列表，每个示例包含code和metadata
        """
        query_embedding = self._get_embedding(query)
        if not query_embedding:
            return []
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        matches = []
        for i, (doc, meta, distance) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )):
            if distance < similarity_threshold:
                matches.append({
                    "code": doc,
                    "metadata": meta,
                    "similarity_score": 1 - distance  # 转换距离为相似度分数
                })
        
        return matches

    def delete_example(self, example_id: str):
        """删除指定示例
        
        Args:
            example_id: 示例ID
        """
        self.collection.delete(ids=[example_id])

    def update_example(self, example_id: str, 
                      description: str, 
                      keywords: List[str],
                      code: str,
                      model_name: str = ""):
        """更新指定示例
        
        Args:
            example_id: 示例ID
            description: 示例描述
            keywords: 关键词列表
            code: 示例代码
            model_name: 模型名称
        """
        # 先删除旧数据
        self.delete_example(example_id)
        
        # 添加新数据
        text = f"{description} {' '.join(keywords)}"
        embedding = self._get_embedding(text)
        
        if embedding:
            self.collection.add(
                embeddings=[embedding],
                documents=[code],
                metadatas=[{
                    "description": description,
                    "model_name": model_name,
                    "keywords": ",".join(keywords)
                }],
                ids=[example_id]
            ) 