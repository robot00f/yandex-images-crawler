import argparse
import logging
import os
from pathlib import Path
from typing import FrozenSet, List, Tuple, Union


def __start_crawler(start_link: str, load_queue, id: int, headless_mode: bool, is_active):
    try:
        from .yandex_crawler import YandexCrawler
    except ImportError:
        from yandex_crawler import YandexCrawler

    crawler = YandexCrawler(
        start_link=start_link,
        load_queue=load_queue,
        id=id,
        headless_mode=headless_mode,
        is_active=is_active,
    )
    crawler.run()


def __start_loader(
    load_queue,
    image_size: Tuple[int, int],
    image_dir: Union[str, Path],
    skip_files: FrozenSet[str],
    is_active,
):
    try:
        from .image_loader import ImageLoader
    except ImportError:
        from image_loader import ImageLoader

    loader = ImageLoader(
        load_queue=load_queue,
        image_size=image_size,
        image_dir=image_dir,
        skip_files=skip_files,
        is_active=is_active,
    )
    loader.run()


def __start_checker(image_dir: Union[Path, str], image_count: int, is_active):
    try:
        from .count_checker import CountChecker
    except ImportError:
        from count_checker import CountChecker

    checker = CountChecker(
        image_dir=image_dir,
        image_count=image_count,
        is_active=is_active,
    )
    checker.run()


def __download_browser(
    links: List[str],
    image_size: Tuple[int, int],
    image_count: int,
    image_dir: Union[str, Path],
    skip_files: FrozenSet[str],
    loaders_per_link: int,
    headless_mode: bool,
):
    from multiprocessing import Process, Queue, Value

    proc_num = len(links)

    load_queue = Queue(10 * proc_num)

    is_active = Value("i", True)

    crawlers = [
        Process(
            target=__start_crawler,
            args=(links[i], load_queue, i, headless_mode, is_active),
            daemon=True,
        )
        for i in range(proc_num)
    ]

    loaders = [
        Process(
            target=__start_loader,
            args=(load_queue, image_size, image_dir, skip_files, is_active),
            daemon=True,
        )
        for _ in range(proc_num * loaders_per_link)
    ]

    checker = Process(
        target=__start_checker,
        args=(image_dir, image_count, is_active),
        daemon=True,
    )

    processes = []
    processes.extend(crawlers)
    processes.extend(loaders)
    processes.append(checker)

    for process in processes:
        process.start()

    for process in processes:
        process.join()


def download(
    links: List[str],
    image_size: Tuple[int, int],
    image_count: int,
    image_dir: Union[str, Path],
    skip_files: FrozenSet[str],
    loaders_per_link: int,
    headless_mode: bool,
    mode: str = "http",
    page_delay: float = 1.0,
):
    if mode in ("http", "auto"):
        try:
            from .http_crawler import download_http
        except ImportError:
            from http_crawler import download_http

        result = download_http(
            links=links,
            image_size=image_size,
            image_count=image_count,
            image_dir=image_dir,
            skip_files=skip_files,
            loaders_per_link=loaders_per_link,
            page_delay=page_delay,
        )

        if mode == "http":
            if result["captcha_hit"] and not result["reached_target"]:
                logging.warning(
                    "HTTP mode stopped due to Yandex CAPTCHA after downloading %d image(s). "
                    "Re-run with --mode browser (or --mode auto) to continue using Chrome.",
                    result["downloaded"],
                )
            return

        if result["reached_target"]:
            return

        logging.warning(
            "HTTP phase finished with %d new image(s) before reaching target; "
            "falling back to browser mode...",
            result["downloaded"],
        )
        current_files = []
        for _, _, files in os.walk(image_dir):
            current_files.extend(files)
            break
        updated_skip = skip_files.union(
            frozenset(file.split(".")[0] for file in current_files)
        )
        fallback_links = result["remaining_links"] or links
        __download_browser(
            links=fallback_links,
            image_size=image_size,
            image_count=image_count,
            image_dir=image_dir,
            skip_files=updated_skip,
            loaders_per_link=loaders_per_link,
            headless_mode=headless_mode,
        )
        return

    __download_browser(
        links=links,
        image_size=image_size,
        image_count=image_count,
        image_dir=image_dir,
        skip_files=skip_files,
        loaders_per_link=loaders_per_link,
        headless_mode=headless_mode,
    )


def __parse_args():
    parser = argparse.ArgumentParser(description="Yandex Images Crawler", add_help=True)
    parser.add_argument(
        "--links",
        type=str,
        metavar="LINK1,...",
        default=None,
        required=False,
        help="""Full links to image sets for download.
        Links should be separated by commas.
        Each link should lead to an image search result or to an open preview of an image.
        The program will open all links each in its own window.""",
    )
    parser.add_argument(
        "--links-file",
        type=str,
        metavar="FILE",
        default=None,
        required=False,
        help="""Text file with full links to image sets for download.
        Links should be separated by newlines.
        Each link should lead to an image search result or to an open preview of an image.
        The program will open all links each in its own window.""",
    )
    parser.add_argument(
        "--size",
        type=str,
        metavar="WxH",
        default="0x0",
        required=False,
        help="""Minimum size of images to download.
        Width an height should be separated by 'x'.""",
    )
    parser.add_argument(
        "--count",
        type=int,
        metavar="N",
        default=0,
        required=False,
        help="""Required count of images to download.
        Do not set it at all for infinite count.
        A message appears if the desired number of images are downloaded.""",
    )
    parser.add_argument(
        "--dir",
        type=str,
        metavar="DIR",
        default="yandex-images",
        required=False,
        help="Directory for new images.",
    )
    parser.add_argument(
        "--prev-dir",
        type=str,
        metavar="DIR",
        default=None,
        required=False,
        help="""Directory of previously loaded images.
        Program skips the loading of already loaded images in another directory.
        Useful for re-downloading.""",
    )
    parser.add_argument(
        "--loaders-per-link",
        type=int,
        metavar="N",
        default=1,
        required=False,
        help="""Number of loaders per link.
        Use larger values to speed up loading, but take into account your computer's performance.""",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["http", "browser", "auto"],
        default=None,
        required=False,
        help="""Crawling mode:
        'http' (default) uses pure HTTP requests without launching a browser (minimal RAM/CPU).
        'browser' uses Selenium + Chrome (useful for large crawls or solving CAPTCHAs interactively).
        'auto' starts in 'http' mode and automatically falls back to 'browser' mode if CAPTCHA or pagination limit is reached before --count.""",
    )
    parser.add_argument(
        "--delay",
        type=float,
        metavar="SECONDS",
        default=1.0,
        required=False,
        help="Delay in seconds between HTTP page requests (used in 'http' and 'auto' modes).",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        required=False,
        help="""Run the browser in headless mode (implies --mode browser unless --mode is explicitly set).
        You can't fix some problems in browser windows manually, so use this option with caution.""",
    )

    args = parser.parse_args()
    new_args = argparse.Namespace()

    new_args.links = []
    if args.links is not None and args.links_file is not None:
        logging.critical("Provide links via --links only or --links-file only")
        exit(-1)
    if args.links is not None:
        new_args.links = args.links.split(",")
    if args.links_file is not None:
        with open(args.links_file, "r") as f:
            new_args.links = f.read().strip().split()
    if len(new_args.links) == 0:
        logging.critical("Provide links via --links only or --links-file only")
        exit(-1)

    new_args.size = tuple(map(int, args.size.split("x")))

    new_args.count = args.count

    new_args.image_dir = Path(args.dir)
    new_args.image_dir.mkdir(parents=True, exist_ok=True)

    previous_images = []
    for _, _, files in os.walk(new_args.image_dir):
        previous_images.extend(files)
        if new_args.count > 0:
            new_args.count += len(files)
        break

    if args.prev_dir is not None:
        for _, _, files in os.walk(args.prev_dir):
            previous_images.extend(files)

    new_args.skip_files = frozenset([file.split(".")[0] for file in previous_images])

    new_args.loaders_per_link = max(1, args.loaders_per_link)
    new_args.headless_mode = args.headless
    if args.mode is not None:
        new_args.mode = args.mode
    else:
        new_args.mode = "browser" if args.headless else "http"
    new_args.delay = max(0.0, args.delay)

    return new_args


def main():
    logging.basicConfig(format="%(levelname)s - %(asctime)s - %(message)s")
    args = __parse_args()
    download(
        args.links,
        args.size,
        args.count,
        args.image_dir,
        args.skip_files,
        args.loaders_per_link,
        args.headless_mode,
        mode=args.mode,
        page_delay=args.delay,
    )


if __name__ == "__main__":
    main()
