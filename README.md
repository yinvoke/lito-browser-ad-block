# Lito Browser Ad Block

[![许可证](https://img.shields.io/github/license/yinvoke/lito-browser-ad-block?label=%E8%AE%B8%E5%8F%AF%E8%AF%81&style=flat-square)](LICENSE)

Lito Browser 的广告拦截规则上游。同步第三方规则，经过编译和校验后发布至 GitHub Pages。

[项目官网](https://yinvoke.github.io/lito-browser-ad-block/) · [发布清单](https://yinvoke.github.io/lito-browser-ad-block/v1/manifest.txt)

## 订阅地址

```text
https://yinvoke.github.io/lito-browser-ad-block/v2/
```

v2 在 v1 的六个文件之外新增 `privacy_domains.txt`(隐私保护域名表)。
v1 是同一快照的兼容视图(少这一个文件、manifest 相应重写),供旧版 Lito 继续更新。

## 规则来源

| 类型 | 来源 | 采用版本 | 用途 |
|---|---|---|---|
| 网络 | AdGuard DNS filter | 官方 DNS 过滤器 | 广告与跟踪域名 |
| 网络 | HaGeZi Multi Pro | `adblock/pro.txt` | 广告与隐私保护 |
| 网络 | HaGeZi TIF | `adblock/tif.mini.txt` | 恶意软件、诈骗、垃圾邮件与钓鱼域名 |
| 网络 | anti-AD | `domains.txt` | 中文互联网广告域名补充 |
| 隐私 | EasyPrivacy | `easyprivacy.txt` | 第三方跟踪与遥测域名(独立成表,单独归因) |
| 元素隐藏 | AdGuard Chinese | uBlock 格式 `224.txt` | 中文网页元素隐藏与路径例外 |

完整地址和许可证信息见 [`sources.json`](sources.json) 与 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。

## 许可证

构建脚本采用 [GPL-3.0](LICENSE)。第三方规则继续遵循各自的许可证和署名条款。
