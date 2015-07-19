var fs          = require('fs'),
    gulp        = require('gulp'), 
    sass        = require('gulp-ruby-sass') ,
    notify      = require("gulp-notify"), 
    bower       = require('gulp-bower'),
    watch       = require('gulp-watch'),
    uglify      = require('gulp-uglifyjs'),
    prefix      = require('gulp-autoprefixer'),
    livereload  = require('gulp-livereload'),
    csslint     = require('gulp-csslint'),
    json        = JSON.parse(fs.readFileSync('./package.json'));

var config = function(){
    var appName = json.name;

    var path = {
        'bower'  : './bower_components/',
        'assets' : './' + appName + '/assets',
        'static' : './' + appName + '/static'
    };

    return {
        'path': path,
        'scss': {
            'input': path.assets + '/scss/style.scss',
            'include': [
                path.bower  + '/bootstrap-sass/assets/stylesheets',
                path.bower  + '/font-awesome/scss',
                path.bower  + '/pikaday-time/scss/',
                path.assets + '/scss/'
            ],
            'output': path.static + "/css",
            'watch': [
                path.assets + '/scss/**.scss',

            ]
        },
        'icons':{
            'input': [
                path.bower + '/font-awesome/fonts/**.*',
                path.bower + '/bootstrap-sass/assets/fonts/**/*.*'
            ],
            'output': path.static + "/fonts"
        },
        'script':{
            'input' : [
                path.bower  + '/jquery/dist/jquery.js',
                path.bower  + '/bootstrap-sass/assets/javascripts/bootstrap/tab.js',
                path.bower  + '/bootstrap-sass/assets/javascripts/bootstrap/tooltip.js',
                path.bower  + '/moment/moment.js',
                path.bower  + '/moment/locale/pl.js',
                path.bower  + '/pikaday-time/pikaday.js',
                path.assets + '/js/*.js'
            ],
            'output': {
                'dir'     : path.static + "/js",
                'filename': 'script.js'
            },
            'watch': [
                path.assets + '/js/*.js'
            ]
        }
    }
}();

gulp.task('bower', function() { 
    return bower(config.path.bower);
});

gulp.task('icons', function() { 
    return gulp.src(config.icons.input) 
          .pipe(gulp.dest(config.icons.output)); 
});

gulp.task('js', function(){
    return gulp.src(config.script.input)
        .pipe(uglify(config.script.output.filename))
        .pipe(gulp.dest(config.script.output.dir))
        .pipe(livereload());
});

gulp.task('scss', function() { 
    return sass(
            config.scss.input,
            {
                style: 'expanded', 
                loadPath: config.scss.include,
                sourcemap: true
            }
        ) 
        .pipe(prefix("last 1 version", "> 1%", "ie 8", "ie 7"))
        .pipe(gulp.dest(config.scss.output))
          .pipe(livereload()); 
});

// Rerun the task when a file changes
 gulp.task('watch', function() {
     livereload.listen();
    config.scss.watch.forEach(function(path){
        gulp.watch(path, ['scss']); 
    })
    config.script.watch.forEach(function(path){
        gulp.watch(path, ['js']); 
    })
});

  gulp.task('default', ['bower', 'icons', 'js', 'scss', 'watch']);
