import pandas as pd


def add_column_before(df1, df2, column_to_add, target_column, uid_column):
    """Adds a column from df1 to df2 before the target_column based on the uid_column"""
    merged_df = pd.merge(
        df1, df2[[uid_column, column_to_add]], on=uid_column, how="left"
    )
    target_index = merged_df.columns.get_loc(target_column)
    merged_df.insert(target_index, column_to_add, merged_df.pop(column_to_add))
    return merged_df
