#!/usr/bin/bash
#!/bin/bash

# write mysql user and pass in ~/.my.cnf
function query(){
    local pass="x"
    mysqlshow -p${pass} $@  \
        | tail -n +5 \
        | head -n -1 \
        | awk -F '|' '{print $2}' \
        | sed 's/^\s\+\|\s\+\$//g'
}

function process(){
    echo $1
    for db_name in $@; do
        for table_name in $(query ${db_name}); do
            for column_name in $(query ${db_name} ${table_name}); do
                echo -e "${db_name}\t${table_name}\t${column_name}"
            done
        done
    done
}

db_names=(SaleSystem_development SaleSystem_test)
process ${db_names}
