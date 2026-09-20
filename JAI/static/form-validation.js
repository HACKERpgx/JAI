/**
 * JAI shared client-side form validation.
 *
 * Usage:
 *   JAIValidation.attach(form, {
 *     email: [JAIValidation.rules.required(), JAIValidation.rules.email()],
 *     password: [JAIValidation.rules.minLength(8)]
 *   }, async (values, form) => { ...submit... });
 *
 * The attached handler always calls event.preventDefault(); the onValid
 * callback runs only when every rule passes. Failing fields get an inline
 * message rendered directly beneath the input.
 */
(function (global) {
  'use strict';

  var STYLE_ID = 'jai-validation-styles';
  var ERROR_ATTR = 'data-jai-error-for';

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = [
      '.jai-field-error{display:block;margin-top:6px;font-size:13px;line-height:1.35;color:#ff6b6b;}',
      '.jai-input-invalid{border-color:#ff6b6b !important;outline-color:#ff6b6b;}',
      '.jai-form-error{margin:10px 0;font-size:13px;color:#ff6b6b;}'
    ].join('\n');
    document.head.appendChild(style);
  }

  function fieldOf(form, name) {
    return form.querySelector('[name="' + name + '"]') || form.querySelector('#' + name);
  }

  function valueOf(field) {
    if (!field) return '';
    if (field.type === 'checkbox') return field.checked ? 'on' : '';
    return typeof field.value === 'string' ? field.value.trim() : field.value;
  }

  function showFieldError(field, message) {
    if (!field) return;
    clearFieldError(field);
    field.classList.add('jai-input-invalid');
    field.setAttribute('aria-invalid', 'true');
    var error = document.createElement('span');
    error.className = 'jai-field-error';
    error.setAttribute('role', 'alert');
    error.setAttribute(ERROR_ATTR, field.name || field.id || '');
    error.textContent = message;
    field.insertAdjacentElement('afterend', error);
  }

  function clearFieldError(field) {
    if (!field) return;
    field.classList.remove('jai-input-invalid');
    field.removeAttribute('aria-invalid');
    var next = field.nextElementSibling;
    if (next && next.classList && next.classList.contains('jai-field-error')) {
      next.remove();
    }
  }

  function clearErrors(form) {
    Array.prototype.forEach.call(form.querySelectorAll('.jai-field-error'), function (el) {
      el.remove();
    });
    Array.prototype.forEach.call(form.querySelectorAll('.jai-input-invalid'), function (el) {
      el.classList.remove('jai-input-invalid');
      el.removeAttribute('aria-invalid');
    });
  }

  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

  var rules = {
    required: function (message) {
      return function (value) {
        return value ? null : (message || 'This field is required.');
      };
    },
    email: function (message) {
      return function (value) {
        if (!value) return null;
        return EMAIL_RE.test(value) ? null : (message || 'Enter a valid email address.');
      };
    },
    minLength: function (min, message) {
      return function (value) {
        if (!value) return null;
        return value.length >= min
          ? null
          : (message || 'Must be at least ' + min + ' characters.');
      };
    },
    maxLength: function (max, message) {
      return function (value) {
        if (!value) return null;
        return value.length <= max ? null : (message || 'Must be at most ' + max + ' characters.');
      };
    },
    pattern: function (regex, message) {
      return function (value) {
        if (!value) return null;
        return regex.test(value) ? null : (message || 'Invalid format.');
      };
    },
    numberRange: function (min, max, message) {
      return function (value) {
        if (value === '') return null;
        var num = Number(value);
        if (isNaN(num) || num < min || num > max) {
          return message || 'Enter a number between ' + min + ' and ' + max + '.';
        }
        return null;
      };
    },
    matches: function (otherName, message) {
      return function (value, form) {
        var other = fieldOf(form, otherName);
        return value === valueOf(other) ? null : (message || 'Values do not match.');
      };
    },
    anyOf: function (names, message) {
      return function (value, form) {
        var filled = names.some(function (name) {
          return valueOf(fieldOf(form, name)) !== '';
        });
        return filled ? null : (message || 'Fill in at least one field.');
      };
    }
  };

  /**
   * Validate a form against a rule map. Returns { valid, errors, values }
   * and renders inline messages beneath each invalid field.
   */
  function validate(form, ruleMap) {
    injectStyles();
    clearErrors(form);

    var errors = {};
    var values = {};
    var firstInvalid = null;

    Object.keys(ruleMap).forEach(function (name) {
      var field = fieldOf(form, name);
      var value = valueOf(field);
      values[name] = value;

      var checks = ruleMap[name] || [];
      for (var i = 0; i < checks.length; i++) {
        var message = checks[i](value, form);
        if (message) {
          errors[name] = message;
          showFieldError(field, message);
          if (!firstInvalid) firstInvalid = field;
          break;
        }
      }
    });

    if (firstInvalid && typeof firstInvalid.focus === 'function') {
      firstInvalid.focus();
    }

    return { valid: Object.keys(errors).length === 0, errors: errors, values: values };
  }

  /**
   * Intercept the form's submit event, validate, and only call onValid
   * (with the trimmed values) when every field passes.
   */
  function attach(form, ruleMap, onValid) {
    if (!form) return;
    injectStyles();
    form.setAttribute('novalidate', 'novalidate');

    Object.keys(ruleMap).forEach(function (name) {
      var field = fieldOf(form, name);
      if (!field) return;
      var reset = function () { clearFieldError(field); };
      field.addEventListener('input', reset);
      field.addEventListener('change', reset);
    });

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      var result = validate(form, ruleMap);
      if (!result.valid) return;
      onValid(result.values, form, event);
    });
  }

  global.JAIValidation = {
    attach: attach,
    validate: validate,
    rules: rules,
    showFieldError: showFieldError,
    clearFieldError: clearFieldError,
    clearErrors: clearErrors,
    field: fieldOf
  };
})(window);
