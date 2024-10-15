# Accounts Cleaner App

This application scans and cleans unwanted data from social networks and messengers based on specified parameters.
Currently, it supports only Telegram and Instagram.

## Features

- Scans Telegram messages within a specified date range.
- Caches peers and messages for faster processing.
- Filters messages based on user-defined criteria such as links, forwards, and keywords.
- Supports configuration for different types of Telegram dialogs (users, chats, channels).
- Scans Instagram history data (need to request and download separately)

## Prerequisites

- Python
- Docker
- Docker Compose

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/cleanaccs/cleanaccs.git
    cd cleanaccs
    ```

2. Install the required Python packages:
    ```sh
    pip install -r requirements.txt
    ```

3. Set up the Docker environment (optional, for cache):
    ```sh
    docker-compose up -d
    ```

## Configuration

### Configuring Telegram Client App

1. Obtain your `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org).
2. Create a `.env` file in the root directory and add your credentials:
    ```dotenv
    API_ID=your_api_id
    API_HASH=your_api_hash
    ```

### Setting Up Configuration File

1. Copy the `config-template.yaml` to `config.yaml`:
    ```sh
    cp config-template.yaml config.yaml
    ```

2. Edit the `config.yaml` file to set your desired arguments. See `config-template.yaml`

## Usage

1. Run the extraction script:
    ```sh
    python cleanup/docextract/unwanted-extract.py
    ```

2. Run the main script to scan and clean your accounts:
    ```sh
    python cleanup/cleanaccs.py
    ```

3. The results will be saved in the logs.
