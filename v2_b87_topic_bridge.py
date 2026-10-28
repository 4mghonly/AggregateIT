"""Explicit Arabic classifier-to-editorial taxonomy adapter (no prose generation)."""
def editorial_topic(product,topic):
 if product=="arabic":
  mapping={"geopolitics":"political_stability","diplomacy":"diplomacy","security":"security"}
  if topic not in mapping:raise ValueError("unmapped_arabic_editorial_topic")
  return mapping[topic]
 if product=="english":
  if topic not in {"geopolitics","security"}:raise ValueError("unmapped_english_editorial_topic")
  return topic
 raise ValueError("unsupported_editorial_product")
