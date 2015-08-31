'use strict';

module.exports = function (grunt) {

  require('load-grunt-tasks')(grunt);

  var gruntConfig = {
    filename: grunt.option('filename') || 'output.json',
    source: 'templates',
    build: 'rendered'
  };

  grunt.initConfig({

    capitolhttpstester: gruntConfig,

    exec: {
      data: {
        command: 'python capitolhttpstester.py > <%= capitolhttpstester.filename %>'
      },
      build: {
        command: 'python render_template.py <%= capitolhttpstester.filename %>'
      }
    },

    cssmin: {
      build: {
        options: {},
        files: [{
          expand: true,
          cwd: '<%= capitolhttpstester.source %>/css',
          src: 'sunlight.css',
          dest: '<%= capitolhttpstester.source %>/css',
          ext: '.min.css'
        }]
      }
    },

    htmlmin: {
      build: {
        options: {
          collapseWhitespace: true,
          conservativeCollapse: true,
          collapseBooleanAttributes: true,
          removeCommentsFromCDATA: true,
          removeOptionalTags: true
        },
        files: [{
          expand: true,
          cwd: '<%= capitolhttpstester.build %>',
          src: ['test_results.html'],
          dest: '<%= capitolhttpstester.build %>'
        }]
      }
    }

  });

  grunt.registerTask('data', [
    'exec:data'
  ]);

  grunt.registerTask('build', [
    'cssmin:build',
    'exec:build',
    'htmlmin:build'
  ]);

  grunt.registerTask('default', [
    'data',
    'build'
  ]);

}
