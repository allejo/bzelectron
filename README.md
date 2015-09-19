# bzelectron

Meet bzelectron, the first successful child of my [/dev/null](https://github.com/allejo/dev-null) repository. Maintaining several different BZFlag servers requires some form of automation especially when a lot of the servers require different group permission files; e.g. you're running public servers, league servers, private servers.

I noticed that a lot of my permission files shared a lot of similarities, so I thought of a way to "compile" partial group permission files into a single one. Inspired by Sass, the syntax for bzelectron is very similar as well.

This is one of my first few real projects in Python so it may not be the most amazing script but it works as long as you're not dumb enough to mess up the syntax.

## Author

Vladimir "allejo" Jimenez

## Syntax

So what's the syntax look like? Well it's similar to [Sass](http://sass-lang.com) and [YAML](http://yaml.org) combined.

**partials/everyone.pgrp**

```
EVERYONE
    +SPAWN
    +TALK
````

**public.pgrp**

```
$prefix = "ALLEJO"

@include partials/everyone.pgrp

VERIFIED
    @extend EVERYONE
    
    +REPORT

$prefix.COP
    +KICK

$prefix.ADMIN
    @extend $prefix.COP

    +BAN
```

**public_match.pgrp**

```
@include public.pgrp

# Public FMs are allowed, so let everyone /countdown but still keep
# the same permissions as my public servers
EVERYONE
    +COUNTDOWN
```

### Using this

Ok. You may have sold me on this, but how do I use it?

```
python bzelectron.py -i public_match.pgrp -o public.groupdb
```

The `-i` flag tells bzelectron which file to compile and the `-o` flag specifies the output file.

## License

MIT
