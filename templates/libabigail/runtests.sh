#!/bin/bash

{% for lib in package.libs %}
printf "Testing {{ lib }} with abidw\n"
out_dir="/results/{{ tester.name }}/{{ tester.version }}/{{ package.name }}/{{ version }}/"
libdir=$(dirname {{ lib }})
mkdir -p $out_dir/$libdir
time -p abidw {% for include in package.includes %} --hd {{ include }} {% endfor %} /opt/view/{{ lib }} --out-file $out_dir/{{ lib }}.xml > $out_dir/{{ lib }}.xml.log 2>&1
echo $? | abi-decode >> $out_dir/{{ lib }}.xml.log
{% endfor %}
