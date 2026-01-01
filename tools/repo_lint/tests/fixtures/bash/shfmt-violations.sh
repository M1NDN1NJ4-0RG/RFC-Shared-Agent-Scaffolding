#!/bin/bash
# Test fixture for shfmt violations

# Bad indentation (inconsistent tabs/spaces)
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
function bad_indent() {
  echo "two spaces"
    echo "four spaces"
	echo "tab character"
}

# Missing space after if/for/while
if[ -f file ]; then
    echo "no space after if"
fi

# Inconsistent operator spacing
x=1+2
y = 3 + 4
z=  5  +  6

# Bad array formatting
arr=(one two three four)
arr2=( one   two    three )
arr3=(
one
two
three
)

# Inconsistent brace style
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
function style1() {
echo "braces on same line"
}

# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
function style2()
{
echo "braces on new line"
}

# Missing semicolon before done/fi
for i in 1 2 3
do
    echo $i
done

# Bad case statement formatting
case "$1" in
start)
echo "starting"
;;
stop)
echo "stopping"
;;
esac

# Inconsistent quoting
var1="quoted"
var2='single'
var3=unquoted

# Bad function definition style
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
function func1 {
    echo "style 1"
}
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
func2() {
    echo "style 2"
}
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
function func3() {
    echo "style 3"
}

# Trailing whitespace (shfmt removes this)
echo "line with trailing spaces"    

# Multiple blank lines


echo "after blanks"

# Bad here-doc indentation
cat <<EOF
no indent
    some indent
        more indent
EOF

# Inconsistent pipeline formatting
echo "test" |grep pattern|wc -l
echo "test" | grep pattern | wc -l
echo "test"|grep pattern |wc -l
