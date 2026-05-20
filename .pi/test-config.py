#!/usr/bin/env python3
"""
测试配置文件
"""

import yaml
import sys

def test_config():
    """测试配置文件"""
    try:
        # 读取配置
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print("✓ 配置文件格式正确")
        
        # 检查必需字段
        required_sections = ['tikhub', 'openclaw', 'search', 'output', 'analysis', 'logging']
        for section in required_sections:
            if section not in config:
                print(f"✗ 缺少配置节: {section}")
                return False
            print(f"✓ 配置节: {section}")
        
        # 检查 TikHub API Key
        api_key = config['tikhub']['api_key']
        if api_key == "your_tikhub_api_key_here":
            print("⚠  TikHub API Key 未配置")
        else:
            print("✓ TikHub API Key 已配置")
        
        # 检查 OpenClaw API Token
        api_token = config['openclaw']['api_token']
        if api_token == "your_openclaw_token_here":
            print("⚠  OpenClaw API Token 未配置")
        else:
            print("✓ OpenClaw API Token 已配置")
        
        # 检查输出路径
        output_path = config['output']['file_path']
        try:
            import os
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            print(f"✓ 输出路径可写: {output_path}")
        except Exception as e:
            print(f"✗ 输出路径不可写: {e}")
            return False
        
        print("\n配置测试完成！")
        return True
        
    except FileNotFoundError:
        print("✗ 未找到 config.yaml 文件")
        return False
    except yaml.YAMLError as e:
        print(f"✗ 配置文件格式错误: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_config()
    sys.exit(0 if success else 1)
