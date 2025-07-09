## v0.3.0 (2025-07-09)

### Feat

- **extractor**: event extractor logic and implementation with instructor
- **shared**: add key_params functionality to cached decorator
- **shared**: utility function to attach data to coroutine results
- **schedule**: create utility to initialize sqlmodel engine
- **shared**: add key_func param to cached decorator
- **shared**: caching utils: generate_key and cached decorator
- **shared**: CacheBackend protocol with file and memory implementations
- **scraper**: add base_url and element_url_pattern fields to Pagination
- **schedule**: create Event and Venue models
- **shared**: implement utility function build_sqlmodel_type
- **main**: new testing utils
- **scraper**: define PaginationRepo and implement JsonPaginationRepo
- **scraper**: add id field to Pagination
- **scraper**: implement pagination_elements function
- **scraper**: implement pagination_urls function
- **shared**: add pattern parameter into extract_urls
- **scraper**: implement pagination logic via PaginationType and Pagination classes

### Fix

- **scraper**: fix Pagination.urls for case PaginationType.MONTH

### Refactor

- **module**: reorganize modules
- **scraper**: use new Pagination.urls in pagination_elements function
- **scraper**: merge crawler and crawler_result files
- **scraper**: move pagination_urls from application to domain (as Pagination class method)

## v0.2.0 (2025-04-24)

### Feat

- **license**: include GPL3 license
- **main**: write tmp testing main function
- **scraper**: define CrawlResult and Crawler domain classes and implement AiohttpCrawler
- **shared**: implement url utils for filtering html content urls and getting a set of urls from an html page

### Fix

- **scraper**: avoid searching for urls in non html content
