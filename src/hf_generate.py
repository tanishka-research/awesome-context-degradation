"""Hugging Face generator for the Colab run (cycle 6). Imports torch and transformers lazily.

Returns the callable expected by runner.run_jobs: generate(prompt) -> (reply, n_prompt_tokens, n_new_tokens, truncated).

Design choices (declared deviations from the original scripts, see docs/deviation_log.md):
  * The repository prompt is sent as the single user message through the tokenizer's own chat template.
  * Greedy decoding with repetition_penalty set to 1.0 explicitly (the model's default generation
    config may differ; it is printed in the notebook and saved).
  * The reply is strip()-ed, as in the original Llama-2 script.
  * early_stop=True ends generation once the reply has a newline after its first non-blank character.
    The scorer reads only the first line, so the score is unchanged; the notebook checks this on
    development prompts before the main run.
  * No prompt is skipped or truncated; `truncated` is 1 only if prompt + new tokens exceed the context size.
"""
from __future__ import annotations


def make_hf_generator(model, tokenizer, max_new_tokens: int = 100, max_positions: int = 32768,
                      early_stop: bool = True):
    import torch
    from transformers import StoppingCriteria, StoppingCriteriaList

    class FirstLineDone(StoppingCriteria):
        def __init__(self, prompt_len: int):
            self.prompt_len = prompt_len

        def __call__(self, input_ids, scores, **kwargs):
            text = tokenizer.decode(input_ids[0, self.prompt_len:], skip_special_tokens=True)
            done = "\n" in text.lstrip()
            return torch.full((input_ids.shape[0],), done, dtype=torch.bool, device=input_ids.device)

    def generate(prompt: str):
        messages = [{"role": "user", "content": prompt}]
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(text, return_tensors="pt").to(model.device)
        n_prompt = int(inputs["input_ids"].shape[1])
        kwargs = dict(max_new_tokens=max_new_tokens, do_sample=False, repetition_penalty=1.0,
                      temperature=None, top_p=None, top_k=None, pad_token_id=tokenizer.eos_token_id)
        if early_stop:
            kwargs["stopping_criteria"] = StoppingCriteriaList([FirstLineDone(n_prompt)])
        with torch.inference_mode():
            out = model.generate(**inputs, **kwargs)
        new = out[0, n_prompt:]
        reply = tokenizer.decode(new, skip_special_tokens=True).strip()
        return reply, n_prompt, int(new.shape[0]), int(n_prompt + max_new_tokens > max_positions)

    return generate
