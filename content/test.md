
## 类型别名

类型别名（type alias）是一个名字，它是某种类型的同义词。使用类型别名有很多好处，它让复杂的类型名字变得简单明了、易于理解和使用，还有助于程序员清楚地知道使用该类型的真实目的。

有两种方法可用于定义类型别名。传统的方法是使用关键字typedef：

``` cpp
//wages 是double的同义词
typedef double wages;
//base是double的同义词,p是double*的同义词
typedef wages base, *p;
```

**C++11**

新标准规定了一种新的方法，使用别名声明（alias declaration）来定义类型的别名：

``` cpp
//64位整型
using int64_t = long long;
```

这种方法用关键字using作为别名声明的开始，其后紧跟别名和等号，其作用是把等号左侧的名字规定成等号右侧类型的别名。

``` cpp
//定义变量a为64位整型
int64_t a = 10;
```

## 指针、常量和类型别名

如果某个类型别名指代的是复合类型或常量，那么把它用到声明语句里就会产生意想不到的后果。

例如下面的声明语句用到了类型`pstring`，它实际上是类型`char＊`的别名：

``` cpp
typedef char * pstring;
const pstring cstr = 0;
const pstring *ps;
```

上述两条声明语句的基本数据类型都是`const pstring`，和过去一样，`const`是对给定类型的修饰。

`pstring`实际上是指向char的指针，因此，`const pstring`就是指向`char`的常量指针，而非指向常量字符的指针。

## auto类型说明符

编程时常常需要把表达式的值赋给变量，这就要求在声明变量的时候清楚地知道表达式的类型。

然而要做到这一点并非那么容易，有时甚至根本做不到。

为了解决这个问题，C++11新标准引入了auto类型说明符，用它就能让编译器替我们去分析表达式所属的类型。

和原来那些只对应一种特定类型的说明符（比如double）不同，auto让编译器通过初始值来推算变量的类型。显然，auto定义的变量必须有初始值：

``` cpp
//计算求和
int age1 = 20;
int age2 = 35;
auto age_add = age1+age2;
```

auto很有作用，后期我们会学习尾置类型推导，以后再讲。

使用auto也能在一条语句中声明多个变量。因为一条声明语句只能有一个基本数据类型，所以该语句中所有变量的初始基本数据类型都必须一样：

``` cpp
//正确, i是整数，p是整型指针
auto i= 0, * p= &i;
//错误, sz是整型，pi是double
//auto sz = 0, pi = 3.14;
```

## 复合类型、常量和auto

编译器推断出来的auto类型有时候和初始值的类型并不完全一样，编译器会适当地改变结果类型使其更符合初始化规则。

首先，正如我们所熟知的，使用引用其实是使用引用的对象，特别是当引用被用作初始值时，真正参与初始化的其实是引用对象的值。

此时编译器以引用对象的类型作为auto的类型：

``` cpp
int i = 0, &r = i;
// a是一个整数，类型是r所引用的类型
auto a = r;
```

auto一般会忽略掉顶层`const`，同时底层`const`则会保留下来，比如当初始值是一个指向常量的指针时：

``` cpp
{
    int i = 0, &r = i;
    // a是一个整数，类型是r所引用的类型
    auto a = r;
    // cr是一个常量引用，ci是int类型的常量
    const int ci = i, &cr = ci;
    // b是一个整数，ci顶层const被忽略了
    auto b = ci;
    // c是一个整数，cr是ci的别名，ci本身是一个顶层const
    auto c = cr;
    // d 是一个整型指针，i是整型
    auto d = &i;
    // e是一个指向整数常量的指针，对常量对象取地址是一种底层const
    auto e = &ci;
}
```

如果希望推断出的auto类型是一个顶层const，需要明确指出：

``` cpp
//顶层const可显示指定,f是一个const int类型
const auto f = ci;
```

还可以将引用的类型设为auto，此时原来的初始化规则仍然适用：

``` cpp
// g是一个整型常量引用，绑定到ci
auto &g = ci;
//错误，非常量引用不能绑定字面量
//auto &h = 42;
//正确,常量引用可以绑定字面量
const auto &j = 42;
```

要在一条语句中定义多个变量，切记，符号&和＊只从属于某个声明符，而非基本数据类型的一部分，因此初始值必须是同一种类型：

``` cpp
//i为int类型， ci为const int类型， 但是k是int类型，l是int&类型
auto k = ci, &l = i;
//m是对常量的引用，p是指向整数常量的指针
// p为const int*类型
auto &m = ci, *p = &ci;
//错误, i为int类型，&ci的类型为const int*
//auto &n = i, *p2 = &ci;
```

## decltype类型指示符

**C++11**

有时会遇到这种情况：希望从表达式的类型推断出要定义的变量的类型，但是不想用该表达式的值初始化变量。

为了满足这一要求，C++11新标准引入了第二种类型说明符decltype，它的作用是选择并返回操作数的数据类型。在此过程中，编译器分析表达式并得到它的类型，却不实际计算表达式的值：

``` cpp
decltype(f()) sum = x; //sum的类型就是函数f的返回值的类型
```

编译器并不实际调用函数f，而是使用当调用发生时f的返回值类型作为sum的类型。换句话说，编译器为sum指定的类型是什么呢？就是假如f被调用的话将会返回的那个类型。

`decltype`处理顶层`const`和引用的方式与`auto`有些许不同。如果`decltype`使用的表达式是一个变量，则`decltype`返回该变量的类型（包括顶层`const`和引用在内）：

``` cpp
const int ci = 0, &cj = ci;
//x是const int类型
decltype(ci) x = 0;
//y是一个const int&类型，y绑定到x
decltype(cj) y = x;
//错误，z是一个引用,引用必须初始化
//decltype(cj) z;
```

因为`cj`是一个引用，`decltype（cj）`的结果就是引用类型，因此作为引用的z必须被初始化。

需要指出的是，引用从来都作为其所指对象的同义词出现，只有用在`decltype`处是一个例外。

## `decltype`和引用

如果`decltype`使用的表达式不是一个变量，则`decltype`返回表达式结果对应的类型。

有些表达式将向`decltype`返回一个引用类型。

一般来说当这种情况发生时，意味着该表达式的结果对象能作为一条赋值语句的左值：

``` cpp
{
    //decltype的结果可以是引用各类型
    int i = 42, *p = &i, &r = i;
    //正确，假发的结果是int，因此b是一个未初始化的int
    decltype(r + 0) b;
    //错误，c是int&，必须初始化
    //decltype(*p) c;
}
```

因为r是一个引用，因此`decltype（r）`的结果是引用类型。

如果想让结果类型是r所指的类型，可以把r作为表达式的一部分，如r+0，显然这个表达式的结果将是一个具体值而非一个引用。

另一方面，如果表达式的内容是解引用操作，则`decltype`将得到引用类型。正如我们所熟悉的那样，解引用指针可以得到指针所指的对象，而且还能给这个对象赋值。

因此，`decltype（*p）`的结果类型就是int&，而非`int`。`decltype`和`auto`的另一处重要区别是，`decltype`的结果类型与表达式形式密切相关。

有一种情况需要特别注意：对于`decltype`所用的表达式来说，如果变量名加上了一对括号，则得到的类型与不加括号时会有不同。

如果`decltype`使用的是一个不加括号的变量，则得到的结果就是该变量的类型；

如果给变量加上了一层或多层括号，编译器就会把它当成是一个表达式。变量是一种可以作为赋值语句左值的特殊表达式，所以这样的`decltype`就会得到引用类型：

``` cpp
//decltype的表达式如果加上了括号的变量，结果就是引用
//错误，d是int&，必须初始化
//decltype((i)) d;
//正确,e是一个未被初始化的int类型值
decltype(r) e = i;
```

切记：`decltype（（variable））`（注意是双层括号）的结果永远是引用，而`decltype（variable）`结果只有当variable本身就是一个引用时才是引用。

## 工作中的应用

工作中会利用`auto`和`decltype`配合使用，结合模板做类型推导返回动态类型，比如我们在并发编程系列课程中封装提交任务

``` cpp
template <class F, class... Args>
auto commit(F&& f, Args&&... args) -> 
std::future<decltype(std::forward<F>(f)(std::forward<Args>(args)...))> {
    using RetType = decltype(std::forward<F>(f)(std::forward<Args>(args)...));
    if (stop_.load())
        return std::future<RetType>{};
    auto task = std::make_shared<std::packaged_task<RetType()>>(
            std::bind(std::forward<F>(f), std::forward<Args>(args)...));
    std::future<RetType> ret = task->get_future();
    {
        std::lock_guard<std::mutex> cv_mt(cv_mt_);
        tasks_.emplace([task] { (*task)(); });
    }
    cv_lock_.notify_one();
    return ret;
}
```

这段代码大家要学习模板，以及万能引用后才能完全吸收，我们留个伏笔，以后的剧情中会触发。