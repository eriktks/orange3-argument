"""Argument processor module.

This compute the usefulness of arguments that will be used for
pre-filtering the arguments for the following mining steps.
"""

from importlib.util import find_spec
import copy
import math

import spacy
import numpy as np


class ArgumentProcessor:
    """Process argument before mining.

    - Rename argument and score columns;
    - Label arguments by usefulness.
    """

    def __init__(self, df_arguments):
        pipe_name = "en_core_web_md"
        if find_spec(pipe_name) is None:
            spacy.cli.download(pipe_name)

        self.df_arguments = df_arguments
        self.nlp_pipe = spacy.load(pipe_name)

    def argument_topics(self, df_chunks):
        """Compute argument topics."""
        if "topics" in self.df_arguments.columns:
            return

        topics = df_chunks.groupby(by="argument_id", as_index=False).agg(
            {"topic": list}
        )["topic"]
        self.df_arguments["topics"] = topics

    def argument_sentiment(self, df_chunks):
        """Compute argument sentiment."""
        if "sentiment" in self.df_arguments.columns:
            return

        df_temp = df_chunks.groupby(by="argument_id", as_index=False).agg(
            {"rank": list, "polarity_score": list}
        )
        sentiments = df_temp.apply(
            lambda x: np.dot(x["rank"], x["polarity_score"]), axis=1
        )
        sentiments = sentiments / 2 + 0.5  # normalize to (0, 1)
        self.df_arguments["sentiment"] = sentiments

    def argument_coherence(self):
        """Compute argument coherence."""
        if "coherence" in self.df_arguments.columns:
            return
        assert (
            "sentiment" in self.df_arguments.columns
        ), "Should compute sentiment first!"

        def gaussian(x):
            """Gaussian activation function."""
            return math.e ** (-(x**2) / 0.4)

        max_score = self.df_arguments["score"].max() - 1
        coherences = (
            self.df_arguments["sentiment"]
            - (self.df_arguments["score"] - 1) / max_score
        ).apply(gaussian)
        self.df_arguments["coherence"] = coherences

    def get_argument_table(self, df_chunks):
        """Get the processed argument table."""
        self.argument_topics(df_chunks)
        self.argument_sentiment(df_chunks)
        self.argument_coherence()
        return copy.deepcopy(self.df_arguments)
