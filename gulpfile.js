"use strict";
var fs = require('fs'),
    gulp = require('gulp'),
    concat = require('gulp-concat'),
    livereload = require('gulp-livereload'),
    cleanCSS = require('gulp-clean-css'),
    prefix = require('gulp-autoprefixer'),
    rename = require('gulp-rename'),
    sass = require('gulp-sass')(require('sass')),
    uglify = require('gulp-uglify'),
    watch = require('gulp-watch'),
    json = JSON.parse(fs.readFileSync('./package.json'));

var config = (function () {
    var appName = json.name;

    var path = {
        npm: './node_modules/',
        app: './' + appName,
        assets: './' + appName + '/assets',
        static: './' + appName + '/static',
        staticfiles: './staticfiles'
    };

    return {
        path: path,
        scss: {
            input: path.assets + '/scss/style.scss',
            include: [
                path.npm,
                path.npm + '/pikaday-time/scss/',
                path.staticfiles,
                path.assets + '/scss/'
            ],
            output: path.static + "/css",
            watch: [
                path.assets + '/scss/**.scss'
            ]
        },
        icons: {
            input: [
                path.npm + '/font-awesome/fonts/**.*'
            ],
            output: path.static + "/fonts"
        },
        script: {
            input: [
                path.npm + '/jquery/dist/jquery.js',
                path.npm + '/bootstrap-sass/assets/javascripts/bootstrap/tab.js',
                path.npm + '/bootstrap-sass/assets/javascripts/bootstrap/tooltip.js',
                path.npm + '/bootstrap-sass/assets/javascripts/bootstrap/modal.js',
                path.staticfiles + '/autocomplete_light/vendor/select2/dist/js/select2.full.js',
                path.staticfiles + '/autocomplete_light/jquery.init.js',
                path.staticfiles + '/autocomplete_light/autocomplete.init.js',
                path.staticfiles + '/autocomplete_light/forward.js',
                path.staticfiles + '/autocomplete_light/select2.js',
                path.staticfiles + '/tasty_feedback/style.js',
                path.npm + '/chart.js/dist/Chart.js',
                path.npm + '/moment/moment.js',
                path.npm + '/moment/locale/pl.js',
                path.npm + '/pikaday-time/pikaday.js',
                path.npm + '/patternomaly/dist/patternomaly.js',
                path.assets + '/js/*.js',
                path.app + '/navsearch/static/navsearch/*.js',
            ],
            output: {
                dir: path.static + "/js",
                filename: 'script.js'
            },
            watch: [
                path.assets + '/js/*.js'
            ]
        }
    };
}());

console.log(config.script);

gulp.task('icons', function () {
    return gulp.src(config.icons.input)
        .pipe(gulp.dest(config.icons.output));
});

gulp.task('js', function () {
    return gulp.src(config.script.input)
        .pipe(concat(config.script.output.filename))
        .pipe(gulp.dest(config.script.output.dir))
        .pipe(livereload())
        .pipe(uglify())
        .pipe(rename({extname: '.min.js'}))
        .pipe(gulp.dest(config.script.output.dir))
        .pipe(livereload());
});

gulp.task('scss', function () {
    return gulp.src(config.scss.input)
        .pipe(sass(
            {
                style: 'expanded',
                includePaths: config.scss.include
            }
        ))
        .pipe(prefix())
        .pipe(gulp.dest(config.scss.output))
        .pipe(livereload())
        .pipe(rename({extname: '.min.css'}))
        .pipe(cleanCSS({compatibility: 'ie8'}))
        .pipe(gulp.dest(config.scss.output))
        .pipe(livereload());
});

// Rerun the task when a file changes
gulp.task('watch', function () {
    livereload.listen();
    config.scss.watch.forEach(function (path) {
        gulp.watch(path, ['scss']);
    });
    config.script.watch.forEach(function (path) {
        gulp.watch(path, ['js']);
    });
});

gulp.task('build', gulp.series('icons', 'js', 'scss'));

gulp.task('default', gulp.series('build', 'watch'));
