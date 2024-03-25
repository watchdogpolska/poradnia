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
            input: [
                path.assets + '/scss/style.scss',
                // path.npm + '/datatables.net-bs/css/dataTables.bootstrap.css',
                // path.npm + '/datatables.net-bs4/css/dataTables.bootstrap.css',
                path.npm + '/datatables.net-buttons-dt/css/buttons.dataTables.css',
                path.npm + '/datatables.net-dt/css/jquery.dataTables.css',
            ],
            include: [
                path.npm,
                path.npm + '/pikaday-time/scss/',
		        path.npm + '/bootstrap/scss/',
                path.staticfiles,
                path.assets + '/scss/'
            ],
            // output: path.static + "/css",
            output: {
                dir: path.static + "/css",
                filename: 'style.css'
            },
            watch: [
                path.assets + '/scss/**.scss'
            ]
        },
        images: {
            input: [
                path.npm + '/datatables.net-dt/images/sort*.*'
            ],
            output: path.static + "/images"
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
                // path.npm + '/bootstrap/js/dist/tab.js',
                // path.npm + '/bootstrap/js/dist/tooltip.js',
                // path.npm + '/bootstrap/js/dist/modal.js',
                path.staticfiles + '/tasty_feedback/style.js',
                path.npm + '/moment/moment.js',
                path.npm + '/moment/locale/pl.js',
                path.npm + '/pikaday-time/pikaday.js',
                path.npm + '/patternomaly/dist/patternomaly.js',
                path.assets + '/js/*.js',
                path.app + '/navsearch/static/navsearch/*.js',
                path.npm + '/datatables.net/js/jquery.dataTables.js',
                // path.npm + 'datatables.net-bs4/js/dataTables.bootstrap4.js',
                path.npm + '/datatables.net-dt/js/dataTables.dataTables.js',
                path.npm + '/datatables.net-buttons/js/dataTables.buttons.js',
                path.staticfiles + '/ajax_datatable/js/utils.js',
                path.app + '/cases/static/cases/case_datatbles.js',
                path.app + '/advicer/static/advicer/advice_datatbles.js',
                path.app + '/letters/static/letters/letters_datatbles.js',
                path.app + '/events/static/events/events_datatbles.js',
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

gulp.task('images', function () {
    return gulp.src(config.images.input)
        .pipe(gulp.dest(config.images.output));
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
        .pipe(concat(config.scss.output.filename))
        .pipe(gulp.dest(config.scss.output.dir))
        .pipe(livereload())
        .pipe(cleanCSS({compatibility: 'ie8'}))
        .pipe(rename({extname: '.min.css'}))
        .pipe(gulp.dest(config.scss.output.dir))
        .pipe(livereload());
});

// Rerun the task when a file changes
// TODO  - fix watch task - it doesn't work
// gulp.task('watch', function () {
//     livereload.listen();
//     config.scss.watch.forEach(function (path) {
//         gulp.watch(path, ['scss']);
//     });
//     config.script.watch.forEach(function (path) {
//         gulp.watch(path, ['js']);
//     });
// });

gulp.task('build', gulp.series('images','icons', 'js', 'scss'));

// gulp.task('default', gulp.series('build', 'watch'));
gulp.task('default', gulp.series('build'));
