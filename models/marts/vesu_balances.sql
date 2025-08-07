{{
  config(
    materialized = 'incremental',
    unique_key = ['date', 'user', 'asset'],
    incremental_strategy = 'merge'
  )
}}

WITH source AS (
  SELECT * FROM {{ ref('stg_vesu_balances') }}
),

cleaned AS (
  SELECT
    date,
    user,
    asset,
    asset_symbol,
    asset_decimals,
    -- Convert scientific notation to decimal
    CAST(total_supplied_adjusted AS DECIMAL(38,18)) as total_supplied,
    CAST(total_borrowed_adjusted AS DECIMAL(38,18)) as total_borrowed,
    CAST(latest_accumulator AS DECIMAL(38,18)) as rate_accumulator,
    debt_asset,
    debt_asset_symbol,
    debt_decimals,
    -- Convert raw amounts to decimals
    CAST(raw_amount_deposit AS DECIMAL(38,0)) / POWER(10, asset_decimals) as amount_deposited,
    CAST(raw_amount_borrowed AS DECIMAL(38,0)) / POWER(10, COALESCE(debt_decimals, 18)) as amount_borrowed
  FROM source
  WHERE total_supplied_adjusted IS NOT NULL 
    OR total_borrowed_adjusted IS NOT NULL
)

SELECT
  date,
  user,
  asset,
  asset_symbol,
  total_supplied,
  total_borrowed,
  rate_accumulator,
  debt_asset,
  debt_asset_symbol,
  amount_deposited,
  amount_borrowed,
  -- Calculate net position
  COALESCE(total_supplied, 0) - COALESCE(total_borrowed, 0) as net_position,
  -- Add metadata
  CURRENT_TIMESTAMP as _extracted_at
FROM cleaned 