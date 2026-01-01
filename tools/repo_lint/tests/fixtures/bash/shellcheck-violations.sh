#!/bin/bash
# Test fixture for shellcheck violations

# SC2148: missing shebang (already handled above)

# SC2086: double quote to prevent globbing
file=$1
cat $file

# SC2068: double quote array expansions
args=("$@")
echo ${args[@]}

# SC2155: declare and assign separately
export VAR="$(complex_command)"

# SC2034: variable appears unused
unused_var="not used"

# SC2046: quote to prevent word splitting
files=$(ls *.txt)
for f in $(ls); do
    echo $f
done

# SC2006: use $(...) instead of legacy backticks
result=`date`

# SC2116: useless echo
echo $(echo "hello")

# SC2005: useless echo
echo `pwd`

# SC2002: useless cat
cat file.txt | grep pattern

# SC2164: cd without checking if it succeeded
cd /some/directory
pwd

# SC2103: use cd ... || exit to avoid continuing
cd /tmp
cd ..

# SC2112: function keyword is non-standard
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
function bad_func() {
    echo "hello"
}

# SC2166: -a and -o are not recommended
if [ -f file ] -a [ -r file ]; then
    echo "exists and readable"
fi

# SC2006: legacy backticks
result=`command`

# SC2181: check exit code directly
command
if [ $? -ne 0 ]; then
    echo "failed"
fi

# SC2236: use -n instead of ! -z
if [ ! -z "$VAR" ]; then
    echo "not empty"
fi

# SC2166: -a is not recommended
if [ -f file -a -r file ]; then
    cat file
fi

# SC2086: quote this to prevent word splitting
name=$1
touch $name

# SC2223: this expression is constant
if [[ x = x ]]; then
    echo "always true"
fi

# SC2115: use "${var:?}" to ensure this never expands to /
rm -rf $PREFIX/

# SC2076: don't quote right-hand side of =~
if [[ "$var" =~ "pattern" ]]; then
    echo "match"
fi

# SC2143: use grep -q instead
if [ "$(ps aux | grep process)" ]; then
    echo "found"
fi

# SC2006: backticks are deprecated
output=`ls`

# SC2230: which is non-standard
if [ -x "$(which command)" ]; then
    echo "found"
fi
