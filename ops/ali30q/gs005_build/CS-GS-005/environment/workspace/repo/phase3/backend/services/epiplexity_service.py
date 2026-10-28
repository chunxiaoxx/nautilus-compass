"""
Epiplexity计算服务
实现Epiplexity核心计算算法
"""
from typing import Dict, Optional
import re
import logging

logger = logging.getLogger(__name__)


class EpiplexityService:
    """Epiplexity计算服务"""

    @staticmethod
    def calculate_epiplexity(
        content: str,
        content_type: str = "TEXT",
        context: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        计算Epiplexity评分

        公式: epiplexity = (SC^0.4) × (LC^0.4) × (T^0.2)

        参数:
        - content: 内容文本
        - content_type: 内容类型 (CODE, TEXT, CONCEPT, etc)
        - context: 上下文信息

        返回:
        {
            "structural_complexity": 0.75,
            "learnable_content": 0.82,
            "transferability": 0.68,
            "epiplexity_score": 0.75
        }
        """
        # 分析三个维度
        sc = EpiplexityService.analyze_structural_complexity(content, content_type)
        lc = EpiplexityService.analyze_learnable_content(content, content_type)
        t = EpiplexityService.analyze_transferability(content, context or {})

        # 计算综合评分 (加权几何平均)
        epiplexity_score = (sc ** 0.4) * (lc ** 0.4) * (t ** 0.2)

        logger.info(f"Calculated epiplexity: SC={sc:.3f}, LC={lc:.3f}, T={t:.3f}, Score={epiplexity_score:.3f}")

        return {
            "structural_complexity": round(sc, 3),
            "learnable_content": round(lc, 3),
            "transferability": round(t, 3),
            "epiplexity_score": round(epiplexity_score, 3)
        }

    @staticmethod
    def analyze_structural_complexity(content: str, content_type: str) -> float:
        """
        分析结构复杂性

        因素:
        - 嵌套深度
        - 依赖关系数量
        - 模式复杂度
        - 抽象层次

        返回: 0.0-1.0
        """
        if not content or len(content.strip()) == 0:
            return 0.0

        complexity_score = 0.0

        # 1. 长度复杂性 (20%)
        length = len(content)
        if length < 100:
            length_score = 0.2
        elif length < 500:
            length_score = 0.4
        elif length < 1000:
            length_score = 0.6
        elif length < 5000:
            length_score = 0.8
        else:
            length_score = 1.0
        complexity_score += length_score * 0.2

        # 2. 嵌套深度 (30%)
        if content_type == "CODE":
            # 计算括号嵌套深度
            max_depth = 0
            current_depth = 0
            for char in content:
                if char in '({[':
                    current_depth += 1
                    max_depth = max(max_depth, current_depth)
                elif char in ')}]':
                    current_depth = max(0, current_depth - 1)

            depth_score = min(1.0, max_depth / 10.0)  # 10层为满分
        else:
            # 文本嵌套 (段落、列表等)
            lines = content.split('\n')
            indented_lines = sum(1 for line in lines if line.startswith((' ', '\t')))
            depth_score = min(1.0, indented_lines / len(lines) if lines else 0)

        complexity_score += depth_score * 0.3

        # 3. 关键词密度 (30%)
        keywords = ['function', 'class', 'if', 'for', 'while', 'import', 'def', 'return']
        keyword_count = sum(content.lower().count(kw) for kw in keywords)
        keyword_score = min(1.0, keyword_count / 20.0)  # 20个关键词为满分
        complexity_score += keyword_score * 0.3

        # 4. 行数复杂性 (20%)
        lines = content.split('\n')
        line_count = len([line for line in lines if line.strip()])
        if line_count < 10:
            line_score = 0.2
        elif line_count < 50:
            line_score = 0.4
        elif line_count < 100:
            line_score = 0.6
        elif line_count < 200:
            line_score = 0.8
        else:
            line_score = 1.0
        complexity_score += line_score * 0.2

        return min(1.0, complexity_score)

    @staticmethod
    def analyze_learnable_content(content: str, content_type: str) -> float:
        """
        分析可学习内容

        因素:
        - 新概念数量
        - 知识密度
        - 信息熵
        - 可理解性

        返回: 0.0-1.0
        """
        if not content or len(content.strip()) == 0:
            return 0.0

        learnability_score = 0.0

        # 1. 概念密度 (40%)
        # 识别潜在的概念 (大写开头的词、专业术语等)
        words = re.findall(r'\b[A-Z][a-z]+\b', content)
        unique_concepts = len(set(words))
        concept_score = min(1.0, unique_concepts / 30.0)  # 30个概念为满分
        learnability_score += concept_score * 0.4

        # 2. 信息密度 (30%)
        # 计算非重复词汇比例
        all_words = re.findall(r'\b\w+\b', content.lower())
        if all_words:
            unique_ratio = len(set(all_words)) / len(all_words)
            info_score = unique_ratio
        else:
            info_score = 0.0
        learnability_score += info_score * 0.3

        # 3. 结构化程度 (20%)
        # 检查是否有清晰的结构 (标题、列表、代码块等)
        structure_indicators = [
            r'^#+\s',  # Markdown标题
            r'^\d+\.',  # 数字列表
            r'^[-*]\s',  # 无序列表
            r'```',  # 代码块
            r'^\s{4,}',  # 缩进
        ]
        structure_count = sum(
            len(re.findall(pattern, content, re.MULTILINE))
            for pattern in structure_indicators
        )
        structure_score = min(1.0, structure_count / 10.0)
        learnability_score += structure_score * 0.2

        # 4. 可读性 (10%)
        # 简单的可读性评估 (平均句子长度)
        sentences = re.split(r'[.!?]+', content)
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            # 理想句子长度 15-25词
            if 15 <= avg_sentence_length <= 25:
                readability_score = 1.0
            elif 10 <= avg_sentence_length <= 30:
                readability_score = 0.7
            else:
                readability_score = 0.4
        else:
            readability_score = 0.5
        learnability_score += readability_score * 0.1

        return min(1.0, learnability_score)

    @staticmethod
    def analyze_transferability(content: str, context: Dict) -> float:
        """
        分析可迁移性

        因素:
        - 通用性
        - 抽象程度
        - 适用范围
        - 依赖程度

        返回: 0.0-1.0
        """
        if not content or len(content.strip()) == 0:
            return 0.0

        transferability_score = 0.0

        # 1. 通用性 (40%)
        # 检查是否包含特定领域的术语
        specific_terms = ['specific', 'custom', 'hardcoded', 'localhost', 'test']
        generic_terms = ['general', 'abstract', 'interface', 'pattern', 'template']

        specific_count = sum(content.lower().count(term) for term in specific_terms)
        generic_count = sum(content.lower().count(term) for term in generic_terms)

        if specific_count + generic_count > 0:
            generality_score = generic_count / (specific_count + generic_count)
        else:
            generality_score = 0.5  # 默认中等通用性
        transferability_score += generality_score * 0.4

        # 2. 抽象程度 (30%)
        # 检查抽象概念的使用
        abstract_indicators = ['abstract', 'interface', 'base', 'generic', 'template', 'pattern']
        abstract_count = sum(content.lower().count(ind) for ind in abstract_indicators)
        abstract_score = min(1.0, abstract_count / 5.0)
        transferability_score += abstract_score * 0.3

        # 3. 依赖程度 (20%)
        # 检查外部依赖
        dependency_indicators = ['import', 'require', 'include', 'from', 'using']
        dependency_count = sum(content.lower().count(ind) for ind in dependency_indicators)
        # 依赖越少，可迁移性越高
        dependency_score = max(0.0, 1.0 - (dependency_count / 10.0))
        transferability_score += dependency_score * 0.2

        # 4. 文档完整性 (10%)
        # 检查是否有注释和文档
        comment_indicators = ['#', '//', '/*', '"""', "'''"]
        comment_count = sum(content.count(ind) for ind in comment_indicators)
        doc_score = min(1.0, comment_count / 5.0)
        transferability_score += doc_score * 0.1

        return min(1.0, transferability_score)

    @staticmethod
    def determine_complexity_level(epiplexity_score: float) -> str:
        """
        根据Epiplexity评分确定复杂性等级

        返回: LOW, MEDIUM, HIGH
        """
        if epiplexity_score < 0.3:
            return "LOW"
        elif epiplexity_score < 0.7:
            return "MEDIUM"
        else:
            return "HIGH"
