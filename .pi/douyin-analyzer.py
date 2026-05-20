#!/usr/bin/env python3
"""
抖音视频分析工具
功能：搜索抖音视频，获取数据，使用 LLM 分析并生成反馈
"""

import asyncio
import httpx
import yaml
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class DouyinAnalyzer:
    def __init__(self, config_path: str = "config.yaml"):
        """初始化分析器"""
        self.config = self._load_config(config_path)
        self._setup_logging()
        
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            self._validate_config(config)
            return config
        except FileNotFoundError:
            print(f"配置文件 {config_path} 不存在，请先创建")
            raise
        except yaml.YAMLError as e:
            print(f"配置文件格式错误: {e}")
            raise
    
    def _validate_config(self, config: Dict) -> None:
        """验证配置"""
        required_keys = ['tikhub', 'openclaw', 'search', 'output', 'analysis']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"配置文件缺少必需的字段: {key}")
        
        # 检查 API Key
        if config['tikhub']['api_key'] == "your_tikhub_api_key_here":
            print("警告：请先配置 TikHub API Key")
        if config['openclaw']['api_token'] == "your_openclaw_token_here":
            print("警告：请先配置 OpenClaw API Token")
    
    def _setup_logging(self) -> None:
        """设置日志"""
        logging.basicConfig(
            level=getattr(logging, self.config['logging']['level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config['logging']['file'], encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def search_douyin(self, keyword: str, count: int = 10) -> List[Dict]:
        """
        搜索抖音视频
        
        Args:
            keyword: 搜索关键词
            count: 返回数量
            
        Returns:
            视频列表
        """
        url = f"{self.config['tikhub']['base_url']}/douyin/video/search"
        params = {
            "keyword": keyword,
            "count": count
        }
        headers = {
            "Authorization": f"Bearer {self.config['tikhub']['api_key']}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                self.logger.info(f"搜索关键词 '{keyword}' 成功，找到 {len(data.get('data', []))} 个视频")
                return data.get('data', [])
        except httpx.HTTPError as e:
            self.logger.error(f"搜索失败: {e}")
            return []
    
    async def get_video_detail(self, video_id: str) -> Optional[Dict]:
        """
        获取视频详细信息
        
        Args:
            video_id: 视频 ID
            
        Returns:
            视频详细信息
        """
        url = f"{self.config['tikhub']['base_url']}/douyin/video/detail"
        params = {"video_id": video_id}
        headers = {
            "Authorization": f"Bearer {self.config['tikhub']['api_key']}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            self.logger.error(f"获取视频详情失败: {e}")
            return None
    
    async def analyze_video(self, video: Dict) -> Dict:
        """
        分析视频并生成反馈
        
        Args:
            video: 视频数据
            
        Returns:
            分析结果
        """
        prompt = self._build_analysis_prompt(video)
        
        payload = {
            "model": "openclaw",
            "input": prompt
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.config['openclaw']['api_url'],
                    json=payload,
                    headers={"Authorization": f"Bearer {self.config['openclaw']['api_token']}"}
                )
                response.raise_for_status()
                result = response.json()
                
                self.logger.info(f"分析视频 '{video.get('title', '未知')}' 成功")
                return {
                    "video": video,
                    "analysis": result.get('choices', [{}])[0].get('message', {}).get('content', ''),
                    "timestamp": datetime.now().isoformat()
                }
        except httpx.HTTPError as e:
            self.logger.error(f"分析失败: {e}")
            return None
    
    def _build_analysis_prompt(self, video: Dict) -> str:
        """构建分析提示词"""
        style = self.config['analysis']['style']
        
        if style == "concise":
            prompt = f"""分析这个抖音视频，请简洁回答（每项 50 字内）：

标题：{video.get('title', '未知')}
描述：{video.get('desc', '无')}
播放量：{video.get('play_count', 0)}
点赞数：{video.get('like_count', 0)}

请生成：
1. 内容分析
2. 数据分析
3. 改进建议
4. {self.config['analysis']['topics_count']}个话题标签
"""
        else:  # detailed
            prompt = f"""详细分析这个抖音视频：

标题：{video.get('title', '未知')}
描述：{video.get('desc', '无')}
作者：{video.get('author', {}).get('nickname', '未知')}
播放量：{video.get('play_count', 0)}
点赞数：{video.get('like_count', 0)}
评论数：{video.get('comment_count', 0)}
分享数：{video.get('share_count', 0)}

请提供：
1. 内容分析（类型、风格、受众、创意点）
2. 数据分析（表现如何、互动率、优劣势）
3. {self.config['analysis']['suggestions_count']}条改进建议
4. {self.config['analysis']['topics_count']}个相关话题标签
"""
        return prompt
    
    async def analyze_batch(self, keyword: str) -> List[Dict]:
        """
        批量分析视频
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            分析结果列表
        """
        self.logger.info(f"开始批量分析，关键词: {keyword}")
        
        # 搜索视频
        videos = await self.search_douyin(
            keyword,
            count=self.config['search']['default_count']
        )
        
        if not videos:
            self.logger.warning("没有找到视频")
            return []
        
        # 限制分析数量
        videos_to_analyze = videos[:self.config['search']['max_videos']]
        self.logger.info(f"将分析 {len(videos_to_analyze)} 个视频")
        
        # 并行分析
        tasks = [self.analyze_video(video) for video in videos_to_analyze]
        results = await asyncio.gather(*tasks)
        
        # 过滤掉失败的结果
        valid_results = [r for r in results if r is not None]
        
        self.logger.info(f"分析完成，成功 {len(valid_results)}/{len(videos_to_analyze)}")
        
        return valid_results
    
    def save_results(self, results: List[Dict]) -> None:
        """保存结果"""
        if not self.config['output']['save_to_file']:
            return
        
        file_path = Path(self.config['output']['file_path'])
        
        # 读取已有结果
        existing_results = []
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    existing_results = json.load(f)
                except json.JSONDecodeError:
                    pass
        
        # 追加新结果
        existing_results.extend(results)
        
        # 保存
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(existing_results, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"结果已保存到 {file_path}")
    
    async def run(self, keyword: Optional[str] = None) -> List[Dict]:
        """
        运行分析
        
        Args:
            keyword: 搜索关键词（可选，默认使用配置文件中的）
            
        Returns:
            分析结果
        """
        keyword = keyword or self.config['search']['default_keyword']
        
        results = await self.analyze_batch(keyword)
        
        if results:
            self.save_results(results)
        
        return results


async def main():
    """主函数"""
    import sys
    
    # 解析参数
    keyword = None
    if len(sys.argv) > 1:
        keyword = sys.argv[1]
    
    # 创建分析器
    analyzer = DouyinAnalyzer()
    
    # 运行分析
    results = await analyzer.run(keyword)
    
    # 打印结果
    print(f"\n分析完成，共 {len(results)} 个视频\n")
    for i, result in enumerate(results, 1):
        video = result['video']
        analysis = result['analysis']
        print(f"【{i}】{video.get('title', '未知')}")
        print(f"{analysis}\n")


if __name__ == "__main__":
    asyncio.run(main())
