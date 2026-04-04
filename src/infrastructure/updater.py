import httpx
import logging
from typing import Dict, Any, Optional

class GitHubUpdater:
    """
    负责检查 GitHub 上的最新版本发布。
    """
    def __init__(self, repo: str = "kellyson520/Thesis-format-check"):
        self.repo = repo
        self.api_url = f"https://api.github.com/repos/{repo}/releases/latest"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ThesisChecker-Engine"
        }

    @staticmethod
    def compare_version(remote_v: str, local_v: str) -> bool:
        """
        语义化版本对比：如果 remote_v > local_v 则返回 True。
        支持 v1.2.3 或 1.2.3 格式。
        """
        try:
            r_parts = [int(''.join(filter(str.isdigit, p))) for p in remote_v.lstrip('v').split('.')]
            l_parts = [int(''.join(filter(str.isdigit, p))) for p in local_v.lstrip('v').split('.')]
            
            # 补齐长度以便对比
            max_len = max(len(r_parts), len(l_parts))
            r_parts += [0] * (max_len - len(r_parts))
            l_parts += [0] * (max_len - len(l_parts))
            
            for r, l in zip(r_parts, l_parts):
                if r > l: return True
                if r < l: return False
            return False
        except Exception:
            # 容错处理：若非数字格式，简单对比字符串
            return remote_v != local_v

    async def check_latest(self, current_version: str) -> Dict[str, Any]:
        """
        异步获取最新版本信息并对比。
        """
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(self.api_url, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    latest_tag = data.get("tag_name", "")
                    
                    if not latest_tag:
                        return {"has_update": False, "error": "No tag found"}
                    
                    has_update = self.compare_version(latest_tag, current_version)
                    
                    return {
                        "has_update": has_update,
                        "current":    current_version,
                        "latest":     latest_tag,
                        "changelog":  data.get("body", "无更新日志描述"),
                        "pub_date":   data.get("published_at", ""),
                        "url":        data.get("html_url", ""),
                    }
                elif response.status_code == 404:
                    return {"has_update": False, "error": "Repo or release not found"}
                else:
                    return {"has_update": False, "error": f"API Error: {response.status_code}"}
        except httpx.ConnectError:
            return {"has_update": False, "error": "无法连接 GitHub (Network Unreachable)"}
        except httpx.TimeoutException:
            return {"has_update": False, "error": "连接超时 (GitHub Timeout)"}
        except Exception as e:
            return {"has_update": False, "error": f"Unknown check failure: {str(e)}"}
