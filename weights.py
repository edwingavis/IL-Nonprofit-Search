def inc_list(column_name, weight_list):
    rowid = 1 
    c.execute('''ALTER TABLE mcp ADD ?''', [column_name])
    for weight in weight_list:
        c.execute('''UPDATE mcp SET ? = ? WHERE rowid = ?;''', [column_name, weight, rowid])
        rowid += 1