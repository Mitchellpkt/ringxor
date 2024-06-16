from typing import Type, Dict, Set, List, Tuple, Union, Any, Collection
import itertools
from multiprocessing import Pool, cpu_count
from tqdm.auto import tqdm
from loguru import logger

# This aliasing is temporary, until the schema is finalized
key_image_pointer: Type = Union[int, str, Any]
output_pointer: Type = Union[int, str, Any]
ring_vector: Type = Set[output_pointer]
ring_bucket: Type = Dict[key_image_pointer, ring_vector]
edge: Type = Dict[str, Any]


def process_bucket_single_thread_core(
    rings: ring_bucket,
    index_pairs: Union[List[Tuple[int, int]], None],
    diagnostic_level: int = 1,
    show_progress_bar: bool = True,
    verbosity_level: int = 1,
) -> List[edge]:
    """
    Core function - you do not need to interact with this directly, use `process_bucket()` below
    This takes a batch of index pairs and processes the rings in a single thread.

    :param rings: bucket of rings to analyze
    :param index_pairs: list of index pairs to process. If None provided, checks all possible combinations
    :param diagnostic_level: 0 = no diagnostics, 1 = include match_key_image_pointer
    :param show_progress_bar: show a progress bar
    :param verbosity_level: 0 = silent
    :return: identified transaction tree edges in the form of {"key_image_pointer": key_image, "output_pointer": output}
    """
    # If no index pairs are provided (could be None, (), {}, [], etc...), use all possible combinations
    if not index_pairs:
        index_pairs = list(itertools.product(list(rings.keys()), list(rings.keys())))
    if verbosity_level:
        logger.info(f"Processing {len(index_pairs)} index pairs")

    # Avoid redundant checks by only crunching the upper triangle of the index pair matrix
    key_image_pointer_pairs: Set[Tuple[key_image_pointer, key_image_pointer]] = {
        (ind1, ind2) for ind1, ind2 in tqdm(index_pairs) if ind2 > ind1
    }
    if verbosity_level:
        logger.info(f"Reduced to {len(key_image_pointer_pairs)} index pairs")

    # Process the bucket
    edges: List[edge] = []
    if show_progress_bar:
        p = tqdm(key_image_pointer_pairs, mininterval=1)
    else:
        p = key_image_pointer_pairs
    for key_image_pointer_left, key_image_pointer_right in p:
        ring_left: ring_vector = rings[key_image_pointer_left]
        ring_right: ring_vector = rings[key_image_pointer_right]
        # Do we have a singleton?
        if len(ring_left & ring_right) == len(ring_left) - 1:
            left_edge: Dict[str, Any] = {
                "key_image_pointer": key_image_pointer_left,
                "output_pointer": (ring_left - ring_right).pop(),
            }
            if diagnostic_level > 0:
                left_edge["match_key_image_pointer"] = key_image_pointer_right
            edges.append(left_edge)

            right_edge: Dict[str, Any] = {
                "key_image_pointer": key_image_pointer_right,
                "output_pointer": (ring_right - ring_left).pop(),
            }
            if diagnostic_level > 0:
                right_edge["match_key_image_pointer"] = key_image_pointer_left
            edges.append(right_edge)

    return edges


def process_bucket(
    rings: ring_bucket,
    index_pairs: Union[None, Collection[Tuple[int, int]]] = None,
    num_workers: Union[int, None] = None,
    diagnostic_level: int = 1,
    verbosity_level: int = 1,
) -> List[edge]:
    """
    This function takes a bucket of rings and processes them to identify transaction tree edges from singletons
    that arise from XORing ring pairs (i.e. symmetric set difference)

    :param rings: bucket of rings to analyze
    :param index_pairs: list of index pairs to process. If None provided, checks all possible combinations
    :param num_workers: number of workers to use. If None provided, uses all available cores
    :param diagnostic_level: 0 = no diagnostics, 1 = include match_key_image_pointer
    :param verbosity_level: 0 = silent
    :return: identified transaction tree edges in the form of {"key_image_pointer": key_image, "output_pointer": output}
    """
    if verbosity_level:
        logger.info(f"Processing {len(rings)} rings")

    # If no index pairs are provided, use all possible combinations
    if index_pairs is None:
        index_pairs = list(itertools.product(list(rings.keys()), list(rings.keys())))
    if verbosity_level:
        logger.info(f"Processing {len(index_pairs)} index pairs")

    # Avoid redundant checks by only crunching the upper triangle of the index pair matrix
    key_image_pointer_pairs: List[Tuple[key_image_pointer, key_image_pointer]] = [
        (ind1, ind2) for ind1, ind2 in tqdm(index_pairs, mininterval=1) if ind2 > ind1
    ]
    if verbosity_level:
        logger.info(f"Reduced to {len(key_image_pointer_pairs)} index pairs")

    # Use all available cores unless specified otherwise
    if num_workers is None:
        num_workers: int = cpu_count()

    if num_workers <= 1:
        # If we only have one worker, just run the single-threaded version
        return process_bucket_single_thread_core(rings, index_pairs=key_image_pointer_pairs)
    else:
        # Split the work into chunks
        batches = [list(key_image_pointer_pairs)[i::num_workers] for i in range(num_workers)]
        if verbosity_level:
            logger.info(f"Split work into {num_workers} batches")
        iterable = [(rings, batch, diagnostic_level) for batch in batches]
        if verbosity_level:
            logger.info(f"Starting parallel processing with {num_workers} workers")

        # Process the chunks in parallel
        with Pool(processes=num_workers) as pool:
            results: List[List[edge]] = pool.starmap(
                process_bucket_single_thread_core,
                iterable,
            )
        if verbosity_level:
            logger.info(f"Processed {len(results)} result batches")

        # Combine the results
        edges: List[edge] = []
        for result in results:
            edges.extend(result)
        if verbosity_level:
            logger.info(f"Reshaped to {len(edges)} edges")

        return edges
