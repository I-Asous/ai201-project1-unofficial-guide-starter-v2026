"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug — Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns — the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.
"""

import re
from dataclasses import dataclass

import config
from ingest import Document


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _split_title(text: str) -> tuple[str, str]:
    """
    Separate a document's title line from its body.

    Every document in campus_life opens with a short title line ("Laundry in
    Fenwick Court") followed by a blank line. The body often never repeats it,
    so a chunk that loses the title can't be told apart from its neighbours.
    Returns ("", text) when the first line doesn't look like a title.
    """
    head, sep, rest = text.partition("\n\n")
    if sep and "\n" not in head and len(head) <= 100 and not head.endswith((".", "!", "?")):
        return head, rest
    return "", text


def _pack(units: list[tuple[str, str]], budget: int) -> list[str]:
    """
    Greedily join (text, separator-before) units into pieces no longer than
    budget. Never cuts a unit.
    """
    pieces: list[str] = []
    current = ""
    for text, sep in units:
        candidate = f"{current}{sep}{text}" if current else text
        if current and len(candidate) > budget:
            pieces.append(current)
            current = text
        else:
            current = candidate
    if current:
        pieces.append(current)
    return pieces


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Split on the document's own structure: whole post, else paragraph, else
    sentence. Every chunk carries its document's title line.

    - A document that fits in config.CHUNK_SIZE stays ONE chunk. In campus_life
      that is every document (the longest is well under 700 characters), so the
      post is the unit of retrieval and no thought is ever cut.
    - A longer document is packed paragraph by paragraph. A paragraph that is
      itself too long is packed sentence by sentence. Only a single sentence
      longer than the budget is ever cut mid-sentence, and it is cut on a word.
    - Every piece after the split is prefixed with the title, so "Machines take
      $1.75 wash" is never separated from "Laundry in Aldridge Hall".
    - Overlap is 0. Chunks end on paragraph or sentence boundaries, so there is
      no half-thought to repeat; the repeated title is the shared context.

    Chunks are marked produced_by "chunker.py::split_documents".
    """
    size = config.CHUNK_SIZE
    chunks: list[Chunk] = []

    for doc in documents:
        if len(doc.text) <= size:
            pieces = [doc.text]
        else:
            title, body = _split_title(doc.text)
            prefix = f"{title}\n\n" if title else ""
            budget = size - len(prefix)

            paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
            units: list[tuple[str, str]] = []
            for para in paragraphs:
                if len(para) <= budget:
                    units.append((para, "\n\n"))
                    continue
                sep = "\n\n"        # first sentence starts a paragraph, rest continue it
                for sentence in (x for x in _SENTENCE_END.split(para) if x):
                    while len(sentence) > budget:      # last resort: cut on a word
                        cut = sentence.rfind(" ", 0, budget)
                        cut = cut if cut > 0 else budget
                        units.append((sentence[:cut].strip(), sep))
                        sep = " "
                        sentence = sentence[cut:].strip()
                    if sentence:
                        units.append((sentence, sep))
                        sep = " "

            pieces = [prefix + p for p in _pack(units, budget)]

        for i, piece in enumerate(pieces):
            chunks.append(
                Chunk(
                    text=piece,
                    source=doc.source,
                    index=i,
                    produced_by="chunker.py::split_documents",
                )
            )

    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    docs = load_documents()
    chunks = split_documents(docs)
    print(describe(chunks))

    # Criterion 4: every chunk starts with its document's title line and ends
    # on a sentence boundary. Checked across all chunks, not a sample.
    titles = {d.source: _split_title(d.text)[0] for d in docs}
    no_title = [c.label for c in chunks if not c.text.startswith(titles[c.source])]
    mid_sentence = [c.label for c in chunks if not c.text.rstrip().endswith((".", "!", "?", ")", '"'))]
    print(f"criterion 4: {len(no_title)} chunks missing their title, "
          f"{len(mid_sentence)} ending mid-sentence")
    for label in no_title + mid_sentence:
        print(f"  - {label}")
