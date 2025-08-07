-- part of a query repo
-- query name: Vesu Daily User Balances
-- query link: https://dune.com/queries/5526654
-- description: Tracks user balances and positions in Vesu protocol, including deposits, borrows, and liquidations


WITH token_prices AS (
  SELECT * FROM query_4607763
), latest_token_prices AS (
  SELECT *
  FROM (
    SELECT *,
      ROW_NUMBER() OVER (PARTITION BY contract_address ORDER BY day DESC) AS rn
    FROM query_4607763
  ) AS sub
  WHERE rn = 1
), is_multiply AS (
  SELECT DISTINCT transaction_hash
  FROM starknet.events
  WHERE CASE WHEN CARDINALITY(keys) >= 1 THEN keys[1] ELSE NULL END IN (
    0x00176572435ba3db5514722152d1b52139784dc247cb39146c98a0a013e07ea3, /* IncreaseLever */
    0x032a51115a09e849099ad0a4554c619ab37b758b97b43efc3c99db9df31b1111 /* DecreaseLever */
  )
), is_liquidate AS (
  SELECT DISTINCT
    transaction_hash,
    CASE WHEN CARDINALITY(keys) >= 6 THEN keys[6] ELSE NULL END AS liquidator
  FROM starknet.events
  WHERE CASE WHEN CARDINALITY(keys) >= 1 THEN keys[1] ELSE NULL END IN (
    0x03731bef77d4371d61d696ce475c60d128c4e2c7bba44336635a540d6b180e88
  )
  AND from_address IN (
    0x02545b2e5d519fc230e9cd781046d3a64e092114f07e44771e0d719d148725ef,
    0x000d8d6dfec4d33bfb6895de9f3852143a17c6f92fd2a21da3d6924d34870160
  )
), intermediary_events AS (
  SELECT
    block_time,
    transaction_hash,
    from_address,
    CASE WHEN CARDINALITY(keys) >= 1 THEN keys[1] ELSE NULL END AS event_selector,
    CASE WHEN CARDINALITY(keys) >= 2 THEN keys[2] ELSE NULL END AS pool_address,
    CASE WHEN CARDINALITY(keys) >= 3 THEN keys[3] ELSE NULL END AS collateral_token,
    CASE WHEN CARDINALITY(keys) >= 4 THEN keys[4] ELSE NULL END AS debt_token,
    CASE WHEN CARDINALITY(keys) >= 5 THEN keys[5] ELSE NULL END AS user_if_liquidate,
    CASE WHEN CARDINALITY(data) >= 1 THEN VARBINARY_TO_UINT256(data[1]) ELSE NULL END AS amount_deposited,
    CASE WHEN CARDINALITY(data) >= 3 THEN VARBINARY_TO_UINT256(data[3]) ELSE NULL END AS collateral_is_negative,
    CASE WHEN CARDINALITY(data) >= 4 THEN VARBINARY_TO_UINT256(data[4]) ELSE NULL END AS collateral_shares_delta,
    CASE WHEN CARDINALITY(data) >= 7 THEN VARBINARY_TO_UINT256(data[7]) ELSE NULL END AS amount_borrowed,
    CASE WHEN CARDINALITY(data) >= 9 THEN VARBINARY_TO_UINT256(data[9]) ELSE NULL END AS debt_is_negative,
    CASE WHEN CARDINALITY(data) >= 10 THEN VARBINARY_TO_UINT256(data[10]) ELSE NULL END AS nominal_debt_delta,
    CASE
      WHEN CARDINALITY(data) >= 14 THEN
        CASE
          WHEN VARBINARY_TO_UINT256(data[14]) = 1 THEN -VARBINARY_TO_UINT256(data[13])
          ELSE VARBINARY_TO_UINT256(data[13])
        END
      ELSE NULL
    END AS bad_debt
  FROM starknet.events
  WHERE (
    CASE WHEN CARDINALITY(keys) >= 1 THEN keys[1] ELSE NULL END
  ) IN (0x003dfe6670b0f4e60f951b8a326e7467613b2470d81881ba2deb540262824f1e,
        0x03731bef77d4371d61d696ce475c60d128c4e2c7bba44336635a540d6b180e88)
  AND from_address IN (
    0x02545b2e5d519fc230e9cd781046d3a64e092114f07e44771e0d719d148725ef,
    0x000d8d6dfec4d33bfb6895de9f3852143a17c6f92fd2a21da3d6924d34870160
  )
  AND DATE(block_time) >= TRY_CAST('2024-07-01' AS DATE)
), accumulator_data AS (
  SELECT
    DATE(block_time) AS date,
    CASE WHEN CARDINALITY(keys) >= 2 THEN keys[2] ELSE NULL END AS pool_address,
    CASE WHEN CARDINALITY(keys) >= 3 THEN keys[3] ELSE NULL END AS asset,
    CASE WHEN CARDINALITY(data) >= 15 THEN VARBINARY_TO_UINT256(data[15]) / 1e18 ELSE NULL END AS last_rate_accumulator
  FROM starknet.events
  WHERE from_address IN (
    0x02545b2e5d519fc230e9cd781046d3a64e092114f07e44771e0d719d148725ef,
    0x000d8d6dfec4d33bfb6895de9f3852143a17c6f92fd2a21da3d6924d34870160
  )
  AND CASE WHEN CARDINALITY(keys) >= 1 THEN keys[1] ELSE NULL END = 0x00e623beb06d0cfbe7f7877cf06290a77c803ca8fde4b54a68b241607c7cc8cc
), events AS (
  SELECT
    DATE(block_time) AS date,
    block_time,
    transaction_hash,
    pool_address,
    collateral_token,
    debt_token,
    amount_deposited,
    collateral_is_negative,
    collateral_shares_delta,
    amount_borrowed,
    debt_is_negative,
    nominal_debt_delta,
    bad_debt,
    user_if_liquidate,
    CASE WHEN transaction_hash IN (SELECT transaction_hash FROM is_multiply) THEN 1 ELSE 0 END AS is_multiply,
    CASE WHEN event_selector IN (0x03731bef77d4371d61d696ce475c60d128c4e2c7bba44336635a540d6b180e88) THEN 1 ELSE 0 END AS is_liquidate
  FROM intermediary_events
), transactions AS (
  SELECT transaction_hash, sender_address
  FROM starknet.transactions
  WHERE transaction_hash IN (SELECT transaction_hash FROM events)
  AND DATE(block_time) >= TRY_CAST('2024-07-01' AS DATE)
), log_data AS (
  SELECT
    e.date,
    e.block_time,
    e.transaction_hash,
    e.collateral_token,
    COALESCE(pc.symbol, pc_last.symbol) AS collateral_token_symbol,
    COALESCE(pc.price, pc_last.price) AS collateral_token_price,
    COALESCE(pc.decimals, pc_last.decimals) AS collateral_token_decimals,
    e.debt_token,
    COALESCE(pd.symbol, pd_last.symbol) AS debt_token_symbol,
    COALESCE(pd.price, pd_last.price) AS debt_token_price,
        COALESCE(pd.decimals, pd_last.decimals) AS debt_token_decimals,

    e.amount_deposited,
    e.amount_deposited / POWER(10, COALESCE(pc.decimals, pc_last.decimals)) AS amount_deposited_adjusted,
    e.collateral_shares_delta,
    e.amount_borrowed,
    e.amount_borrowed / POWER(10, COALESCE(pd.decimals, pd_last.decimals)) AS amount_borrowed_adjusted,
    e.nominal_debt_delta,
    e.bad_debt,
    CASE WHEN e.is_liquidate = 0 THEN t.sender_address ELSE e.user_if_liquidate END AS user,
    e.pool_address,
    p.name AS pool,
    p.owner AS pool_owner,
    e.is_multiply,
    e.is_liquidate,
    e.collateral_is_negative,
    l.liquidator,
    acc.last_rate_accumulator
  FROM events AS e
  LEFT JOIN token_prices AS pc ON e.date = pc.day AND e.collateral_token = pc.contract_address
  LEFT JOIN latest_token_prices AS pc_last ON e.collateral_token = pc_last.contract_address
  LEFT JOIN token_prices AS pd ON e.date = pd.day AND e.debt_token = pd.contract_address
  LEFT JOIN latest_token_prices AS pd_last ON e.debt_token = pd_last.contract_address
  LEFT JOIN query_4686551 AS p ON p.contract_address = e.pool_address
  LEFT JOIN is_liquidate AS l ON l.transaction_hash = e.transaction_hash
  INNER JOIN transactions AS t ON t.transaction_hash = e.transaction_hash
  LEFT JOIN accumulator_data AS acc ON e.date = acc.date AND e.pool_address = acc.pool_address AND e.collateral_token = acc.asset
), aggregated_user_data AS (
  SELECT
    date,
    user,
    collateral_token AS asset,
    collateral_token_symbol AS asset_symbol,
    collateral_token_decimals AS asset_decimals,
    MAX(last_rate_accumulator) AS latest_accumulator,

    SUM(collateral_shares_delta * COALESCE(last_rate_accumulator, 1)) AS total_supplied_adjusted,
    SUM(nominal_debt_delta * COALESCE(last_rate_accumulator, 1)) AS total_borrowed_adjusted,
    SUM(amount_deposited) AS raw_amount_deposit,
    SUM(amount_deposited_adjusted) AS adjusted_amount_deposit,
    debt_token AS debt_asset,
    debt_token_symbol AS debt_asset_symbol,
        debt_token_decimals AS debt_decimals,
    SUM(amount_borrowed) AS raw_amount_borrowed,
    SUM(amount_borrowed_adjusted) AS adjusted_amount_borrowed
  FROM log_data
  WHERE NOT pool IS NULL
  AND ( (is_liquidate = 1 AND collateral_is_negative IN (0, 1)) OR is_liquidate = 0 )
  GROUP BY date, user, collateral_token, collateral_token_symbol, collateral_token_decimals, debt_token, debt_token_symbol, debt_token_decimals
)
SELECT
  date,
  user,
  asset,
  asset_symbol,
    asset_decimals,
  total_supplied_adjusted,
  raw_amount_deposit,
  adjusted_amount_deposit,
    latest_accumulator,

  debt_asset,
  debt_asset_symbol,
        debt_decimals,
  total_borrowed_adjusted,
  raw_amount_borrowed,
  adjusted_amount_borrowed
FROM aggregated_user_data
WHERE total_supplied_adjusted IS NOT NULL OR total_borrowed_adjusted IS NOT NULL;